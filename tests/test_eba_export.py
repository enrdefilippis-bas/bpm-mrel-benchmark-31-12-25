"""Tests for the EBA Pillar 3 export parser."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest

from core.schema import FACT_COLUMNS, Source, Template, UnitType, zero_pad_row_code
from ingestion.eba_export import _infer_unit, _normalize_value, parse_eba_export


DATA = Path(__file__).resolve().parent.parent / "data" / "raw" / "p3mreldata_2025q4.xlsx"


def test_zero_pad_row_code_handles_floats_and_strings():
    assert zero_pad_row_code(10.0) == "0010"
    assert zero_pad_row_code(130) == "0130"
    assert zero_pad_row_code("0050") == "0050"
    assert zero_pad_row_code("  20 ") == "0020"
    assert zero_pad_row_code(None) == ""
    assert zero_pad_row_code(float("nan")) == ""


def test_infer_unit_classifies_ratios_and_amounts():
    assert _infer_unit("3. Own funds and eligible liabilities as a percentage of the TREA", "a. T") == UnitType.RATIO.value
    assert _infer_unit("1. Own funds and eligible liabilities", "a. T") == UnitType.AMOUNT_EUR.value
    assert _infer_unit("2. Total risk exposure amount TREA", "a. T") == UnitType.AMOUNT_EUR.value
    assert _infer_unit("unknown", "") == UnitType.UNKNOWN.value


def test_infer_unit_km2_ratio_rows_override_string_heuristic():
    """KM2 'of which …' sub-rows are ratios even when text reads like an amount."""
    # Row 0050 text looks like an amount but the KM2 row-code override wins.
    assert _infer_unit(
        "EU-3a. Of which own funds and subordinated liabilities",
        "a. T",
        template="K_90.01", row_code="0050",
    ) == UnitType.RATIO.value
    # Non-KM2 templates still fall back to string heuristics.
    assert _infer_unit(
        "EU-3a. Of which own funds and subordinated liabilities",
        "a. T",
        template="K_91.00", row_code="0050",
    ) == UnitType.AMOUNT_EUR.value


def test_normalize_value_standardizes_percent_reporting():
    # Most banks report as decimals — pass through.
    assert _normalize_value(0.3402, UnitType.RATIO.value) == pytest.approx(0.3402)
    # Norwegian SpareBanks etc. report as raw percent (>=1.5) — divide by 100.
    assert _normalize_value(66.35, UnitType.RATIO.value) == pytest.approx(0.6635)
    # Amounts pass through.
    assert _normalize_value(22_074_992_606, UnitType.AMOUNT_EUR.value) == 22_074_992_606
    # None / NaN propagate.
    assert _normalize_value(None, UnitType.RATIO.value) is None
    assert _normalize_value(float("nan"), UnitType.RATIO.value) is None


@pytest.mark.skipif(not DATA.exists(), reason="EBA export not available")
def test_parse_eba_export_produces_canonical_schema():
    facts = parse_eba_export(DATA)
    assert list(facts.columns) == list(FACT_COLUMNS.keys())
    # Every row tagged as EBA-export ingested today (or earlier during CI).
    assert set(facts["source"].unique()) == {Source.EBA_EXPORT.value}
    assert pd.api.types.is_datetime64_dtype(facts["reference_date"])
    assert pd.api.types.is_datetime64_dtype(facts["ingested_at"])


@pytest.mark.skipif(not DATA.exists(), reason="EBA export not available")
def test_parse_eba_export_contains_bpm_km2_headline():
    """BPM's MREL % TREA at 2025-12-31 matches the known 34.02%."""
    facts = parse_eba_export(DATA)
    bpm_lei = "815600E4E6DCD2D25E30"
    date = pd.Timestamp("2025-12-31")
    mrel_pct = facts[
        (facts["entity_lei"] == bpm_lei)
        & (facts["reference_date"] == date)
        & (facts["template"] == Template.KM2.value)
        & (facts["row_code"] == "0040")
        & (facts["col_code"] == "0010")
    ]
    assert len(mrel_pct) == 1
    assert mrel_pct["unit"].iloc[0] == UnitType.RATIO.value
    assert float(mrel_pct["value"].iloc[0]) == pytest.approx(0.3402, abs=1e-4)


@pytest.mark.skipif(not DATA.exists(), reason="EBA export not available")
def test_parse_eba_export_contains_all_three_quarters():
    facts = parse_eba_export(DATA)
    dates = sorted(d.isoformat() for d in facts["reference_date"].dt.date.unique())
    assert "2025-06-30" in dates
    assert "2025-09-30" in dates
    assert "2025-12-31" in dates
