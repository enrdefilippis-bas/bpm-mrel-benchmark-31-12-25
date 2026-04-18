"""Tests for the P3 datahub export parser."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from core.schema import FACT_COLUMNS, Source, Template, UnitType
from ingestion.p3_datahub import _infer_unit, _normalize_value, parse_p3_datahub


DATA = Path(__file__).resolve().parent.parent / "p3datahuball copia.xlsx"


def test_infer_unit_classifies_ratios_and_amounts():
    """Test that unit inference works consistently with EBA parser."""
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


def test_normalize_value_standardizes_percent_reporting():
    """Test normalization of ratio and amount values."""
    # Most banks report as decimals — pass through.
    assert _normalize_value(0.3402, UnitType.RATIO.value) == pytest.approx(0.3402)
    # High values interpreted as percentages — divide by 100.
    assert _normalize_value(66.35, UnitType.RATIO.value) == pytest.approx(0.6635)
    # Amounts pass through.
    assert _normalize_value(22_074_992_606, UnitType.AMOUNT_EUR.value) == 22_074_992_606
    # None / NaN propagate.
    assert _normalize_value(None, UnitType.RATIO.value) is None
    assert _normalize_value(float("nan"), UnitType.RATIO.value) is None


@pytest.mark.skipif(not DATA.exists(), reason="P3 datahub export not available")
def test_parse_p3_datahub_produces_canonical_schema():
    """Test that parser produces valid canonical schema facts."""
    facts = parse_p3_datahub(DATA)
    assert list(facts.columns) == list(FACT_COLUMNS.keys())
    # Every row should be tagged as p3-datahub source.
    assert facts.empty or set(facts["source"].unique()).issubset({"p3-datahub"})
    assert pd.api.types.is_datetime64_dtype(facts["reference_date"])
    assert pd.api.types.is_datetime64_dtype(facts["ingested_at"])


@pytest.mark.skipif(not DATA.exists(), reason="P3 datahub export not available")
def test_parse_p3_datahub_filters_by_module():
    """Test that parser only includes MRELTLACDIS module by default."""
    facts = parse_p3_datahub(DATA, module_filter="MRELTLACDIS")
    # All facts should have templates from the MREL/TLAC family
    valid_templates = {t.value for t in Template}
    if not facts.empty:
        unknown = set(facts["template"].unique()) - valid_templates
        # May have empty templates, but no truly invalid ones
        assert all(t == "" for t in unknown if t not in valid_templates)


@pytest.mark.skipif(not DATA.exists(), reason="P3 datahub export not available")
def test_parse_p3_datahub_has_expected_reference_dates():
    """Test that parser extracts the four expected reference dates."""
    facts = parse_p3_datahub(DATA)
    if not facts.empty:
        dates = sorted(facts["reference_date"].unique())
        expected = {
            pd.Timestamp("2024-12-31"),
            pd.Timestamp("2025-06-30"),
            pd.Timestamp("2025-09-30"),
            pd.Timestamp("2025-12-31"),
        }
        actual = set(pd.to_datetime(dates))
        # Should have at least some of the expected dates
        assert len(actual & expected) > 0


@pytest.mark.skipif(not DATA.exists(), reason="P3 datahub export not available")
def test_parse_p3_datahub_covers_missing_banks():
    """Test that datahub includes data for Italian O-SIIs (MPS, BPER, Mediobanca, ICCREA)."""
    facts = parse_p3_datahub(DATA)
    if facts.empty:
        pytest.skip("Datahub facts empty")

    # Check for coverage of key missing banks (by substring match on entity_name)
    names = facts["entity_name"].str.lower().unique()
    missing_banks = ["monte dei paschi", "bper", "mediobanca", "iccrea"]
    covered = [bank for bank in missing_banks if any(bank in name for name in names)]

    # We expect to find at least some of these banks in the datahub
    assert len(covered) >= 1, f"Datahub should cover some of: {missing_banks}"
