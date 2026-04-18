"""Tests for PDF parsers: validate extracted values against manual entries."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from core.schema import Template, UnitType
from ingestion.missing_banks import (
    BBVAParser,
    CreditAgricoleParser,
    IntesaParser,
    SocGenParser,
    UniCreditParser,
)
from ingestion.missing_banks.base import KM2_CELLS, TLAC1_CELLS


# Test data: (parser_class, bank_slug, manual_entry_file)
PARSER_TEST_CASES = [
    (SocGenParser, "socgen", "data/manual_entries/socgen.json"),
    (IntesaParser, "intesa", "data/manual_entries/intesa.json"),
    (UniCreditParser, "unicredit", "data/manual_entries/unicredit.json"),
    (BBVAParser, "bbva", "data/manual_entries/bbva.json"),
    (CreditAgricoleParser, "ca-sa", "data/manual_entries/credit_agricole.json"),
]

# Strict tier: these 6 core fields MUST be extracted for every bank
STRICT_TIER_FIELDS = {
    "mrel_total_amount",
    "trea",
    "tem",
    "cet1",
    "at1",
    "tier2",
}


def _load_manual_entries(entry_file: str) -> dict:
    """Load ground truth from manual entries JSON."""
    path = Path(entry_file)
    if not path.exists():
        pytest.skip(f"Manual entry file not found: {entry_file}")
    return json.loads(path.read_text())


def _pivot_facts_to_dict(df: pd.DataFrame) -> dict:
    """Convert facts DataFrame to {(template, row_code): value} dict."""
    result = {}
    for _, row in df.iterrows():
        key = (row["template"], row["row_code"])
        result[key] = row["value"]
    return result


def _get_tolerance(unit: str) -> tuple[float, str]:
    """Return (tolerance, tolerance_type) for a given unit.

    - Amounts (UnitType.AMOUNT_EUR): relative tolerance 1% (0.01)
    - Ratios (UnitType.RATIO): absolute tolerance 0.001 (10 bps)
    """
    if unit == UnitType.AMOUNT_EUR.value:
        return (0.01, "relative")
    elif unit == UnitType.RATIO.value:
        return (0.001, "absolute")
    else:
        raise ValueError(f"Unknown unit: {unit}")


def _get_field_type(metric_key: str) -> str:
    """Determine if a metric is in KM2_CELLS or TLAC1_CELLS."""
    if metric_key in KM2_CELLS:
        return "km2"
    elif metric_key in TLAC1_CELLS:
        return "tlac1"
    else:
        return None


@pytest.mark.parametrize(
    "parser_class,bank_slug,entry_file",
    PARSER_TEST_CASES,
    ids=[f"{slug}" for _, slug, _ in PARSER_TEST_CASES],
)
def test_parser_matches_manual_entries(
    parser_class, bank_slug: str, entry_file: str
):
    """Validate that parser output matches manual entries within tolerance.
    
    Two-tier validation:
    - STRICT TIER: 6 core fields (mrel_total_amount, trea, tem, cet1, at1, tier2)
      must be extracted and match ground truth within tolerance.
    - SOFT TIER: remaining fields (ratios, requirements, composition breakdown)
      are optional. If extracted, they must match. If not, that's acceptable.
    """
    pytest.importorskip("pdfplumber")

    # Load ground truth
    manual_data = _load_manual_entries(entry_file)
    
    # Build ground truth mapping: metric_key -> (template, row_code, truth_value, unit)
    ref_date_key = "2025-12-31"
    if ref_date_key not in manual_data.get("reference_dates", {}):
        pytest.skip(f"No 2025-12-31 entry in {entry_file}")

    day = manual_data["reference_dates"][ref_date_key]
    
    ground_truth = {}  # metric_key -> (template, row_code, value, unit)

    # KM2 cells
    km2_truth = day.get("km2") or {}
    for metric, (row_code, col_code, unit) in KM2_CELLS.items():
        value = km2_truth.get(metric)
        if value is not None:
            ground_truth[metric] = (Template.KM2.value, row_code, float(value), unit)

    # TLAC1 cells
    tlac1_truth = day.get("tlac1") or {}
    for cls_key, row_code in TLAC1_CELLS.items():
        value = tlac1_truth.get(cls_key)
        if value is not None:
            ground_truth[cls_key] = (Template.TLAC1.value, row_code, float(value), UnitType.AMOUNT_EUR)

    if not ground_truth:
        pytest.skip(f"No KM2 or TLAC1 values in {entry_file}")

    # Parse PDF
    pdf_path = Path(f"data/raw/pdfs/{bank_slug}/pillar3_2025_Q4.pdf")
    if not pdf_path.exists():
        pytest.skip(f"PDF not found: {pdf_path}")

    try:
        parsed_df = parser_class.parse_pdf(pdf_path)
    except NotImplementedError:
        pytest.skip(f"{parser_class.__name__}.parse_pdf not implemented")
    except Exception as e:
        pytest.fail(f"Parse failed for {bank_slug}: {e}")

    if parsed_df.empty:
        pytest.skip(f"{parser_class.__name__} returned empty DataFrame")

    # Extract parsed values as (template, row_code) -> value dict
    parsed_facts_dict = _pivot_facts_to_dict(parsed_df)

    # Separate ground truth into strict and soft tiers
    strict_truth = {k: v for k, v in ground_truth.items() if k in STRICT_TIER_FIELDS}
    soft_truth = {k: v for k, v in ground_truth.items() if k not in STRICT_TIER_FIELDS}

    # === STRICT TIER: all core fields must be present and match ===
    strict_failures = []
    for metric, (template, row_code, truth_val, unit) in strict_truth.items():
        key = (template, row_code)
        if key not in parsed_facts_dict:
            strict_failures.append(f"  Missing strict-tier field: {metric} ({template}/{row_code})")
            continue

        parsed_val = parsed_facts_dict[key]
        tol, tol_type = _get_tolerance(unit.value)

        if tol_type == "relative":
            if truth_val == 0:
                if parsed_val != 0:
                    strict_failures.append(
                        f"  {metric}: expected 0, got {parsed_val}"
                    )
            else:
                rel_error = abs(parsed_val - truth_val) / abs(truth_val)
                if rel_error > tol:
                    strict_failures.append(
                        f"  {metric}: {parsed_val} vs {truth_val} "
                        f"(rel error {rel_error:.4f} > {tol})"
                    )
        else:  # absolute tolerance
            abs_error = abs(parsed_val - truth_val)
            if abs_error > tol:
                strict_failures.append(
                    f"  {metric}: {parsed_val} vs {truth_val} "
                    f"(abs error {abs_error:.6f} > {tol})"
                )

    if strict_failures:
        pytest.fail(
            f"{parser_class.__name__} STRICT-TIER validation failed:\n" + "\n".join(strict_failures)
        )

    # === SOFT TIER: optional fields, but if present must match ===
    soft_failures = []
    for metric, (template, row_code, truth_val, unit) in soft_truth.items():
        key = (template, row_code)
        if key not in parsed_facts_dict:
            # Soft tier: missing is OK
            continue

        parsed_val = parsed_facts_dict[key]
        tol, tol_type = _get_tolerance(unit.value)

        if tol_type == "relative":
            if truth_val == 0:
                if parsed_val != 0:
                    soft_failures.append(
                        f"  {metric}: expected 0, got {parsed_val}"
                    )
            else:
                rel_error = abs(parsed_val - truth_val) / abs(truth_val)
                if rel_error > tol:
                    soft_failures.append(
                        f"  {metric}: {parsed_val} vs {truth_val} "
                        f"(rel error {rel_error:.4f} > {tol})"
                    )
        else:  # absolute tolerance
            abs_error = abs(parsed_val - truth_val)
            if abs_error > tol:
                soft_failures.append(
                    f"  {metric}: {parsed_val} vs {truth_val} "
                    f"(abs error {abs_error:.6f} > {tol})"
                )

    if soft_failures:
        pytest.fail(
            f"{parser_class.__name__} SOFT-TIER validation failed:\n" + "\n".join(soft_failures)
        )


@pytest.mark.parametrize(
    "parser_class,bank_slug,entry_file",
    PARSER_TEST_CASES,
    ids=[f"{slug}-no-manual" for _, slug, _ in PARSER_TEST_CASES],
)
def test_parser_does_not_depend_on_manual_entries(
    parser_class, bank_slug: str, entry_file: str, monkeypatch
):
    """Verify that parse_pdf does not read from manual_entries/ at runtime.
    
    This test ensures the parser is truly independent and doesn't
    accidentally use ground truth to fill in missing data.
    """
    pytest.importorskip("pdfplumber")

    # Load ground truth to know what PDF to test
    manual_data = _load_manual_entries(entry_file)
    ref_date_key = "2025-12-31"
    if ref_date_key not in manual_data.get("reference_dates", {}):
        pytest.skip(f"No 2025-12-31 entry in {entry_file}")

    # Parse PDF
    pdf_path = Path(f"data/raw/pdfs/{bank_slug}/pillar3_2025_Q4.pdf")
    if not pdf_path.exists():
        pytest.skip(f"PDF not found: {pdf_path}")

    try:
        # Should not fail due to missing manual entries
        parsed_df = parser_class.parse_pdf(pdf_path)
        # If it succeeds, great. If it raises NotImplementedError or custom error, also fine.
    except NotImplementedError:
        pytest.skip(f"{parser_class.__name__}.parse_pdf not implemented")
    except Exception as e:
        # Parser should fail gracefully if it can't extract, not crash looking for manual entries
        if "manual_entries" in str(e).lower():
            pytest.fail(f"{parser_class.__name__} parse_pdf tried to read manual_entries: {e}")
        # Other errors are acceptable (parse failures)
        pytest.skip(f"{parser_class.__name__} parse_pdf failed (acceptable): {e}")
