"""Tests for derived metrics."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from core.metrics import attach_bank_meta, km2_wide
from core.peers import BPM_LEI
from core.schema import Source, Template, UnitType, empty_facts
from ingestion.bank_dimension import build_bank_dimension
from ingestion.eba_export import parse_eba_export


DATA = Path(__file__).resolve().parent.parent / "data" / "raw" / "p3mreldata_2025q4.xlsx"


def _fact(lei: str, template: str, row: str, col: str, value: float, date: str, unit: str) -> dict:
    return {
        "entity_lei": lei,
        "entity_name": f"bank-{lei}",
        "country": "Italy",
        "reference_date": pd.Timestamp(date),
        "template": template,
        "row_code": row,
        "row_name": "",
        "col_code": col,
        "col_name": "",
        "open_key": "",
        "raw_value": value,
        "value": value,
        "unit": unit,
        "source": Source.EBA_EXPORT.value,
        "ingested_at": pd.Timestamp.now("UTC").tz_localize(None),
    }


def test_km2_wide_builds_expected_columns_and_derivations():
    rows = [
        _fact("LEI1", Template.KM2.value, "0010", "0010", 22e9, "2025-12-31", UnitType.AMOUNT_EUR.value),
        _fact("LEI1", Template.KM2.value, "0030", "0010", 65e9, "2025-12-31", UnitType.AMOUNT_EUR.value),
        _fact("LEI1", Template.KM2.value, "0040", "0010", 0.34, "2025-12-31", UnitType.RATIO.value),
        _fact("LEI1", Template.KM2.value, "0050", "0010", 0.25, "2025-12-31", UnitType.RATIO.value),
        _fact("LEI1", Template.KM2.value, "0120", "0010", 0.22, "2025-12-31", UnitType.RATIO.value),
    ]
    facts = pd.DataFrame(rows)
    wide = km2_wide(facts)

    assert len(wide) == 1
    row = wide.iloc[0]
    assert row["mrel_total_amount"] == pytest.approx(22e9)
    assert row["trea"] == pytest.approx(65e9)
    assert row["mrel_pct_trea"] == pytest.approx(0.34)
    assert row["subord_pct_trea"] == pytest.approx(0.25)
    assert row["mrel_requirement_trea"] == pytest.approx(0.22)
    # Derived
    assert row["mrel_surplus_trea_pp"] == pytest.approx(0.34 - 0.22)
    assert row["subordination_ratio"] == pytest.approx(0.25 / 0.34)


def test_km2_wide_on_empty_facts_returns_empty_frame():
    wide = km2_wide(empty_facts())
    assert len(wide) == 0


def test_subordination_ratio_handles_zero_mrel_pct():
    rows = [
        _fact("LEI1", Template.KM2.value, "0050", "0010", 0.1, "2025-12-31", UnitType.RATIO.value),
        _fact("LEI1", Template.KM2.value, "0040", "0010", 0.0, "2025-12-31", UnitType.RATIO.value),
    ]
    wide = km2_wide(pd.DataFrame(rows))
    # Division by zero -> NaN, not inf.
    assert pd.isna(wide["subordination_ratio"].iloc[0])


@pytest.mark.skipif(not DATA.exists(), reason="EBA export not available")
def test_metrics_on_real_data_match_bpm_headlines():
    facts = parse_eba_export(DATA)
    banks = build_bank_dimension(facts)
    wide = attach_bank_meta(km2_wide(facts), banks)
    bpm_latest = wide[
        (wide["entity_lei"] == BPM_LEI)
        & (wide["reference_date"] == pd.Timestamp("2025-12-31"))
    ]
    assert len(bpm_latest) == 1
    r = bpm_latest.iloc[0]
    assert r["mrel_pct_trea"] == pytest.approx(0.3402, abs=1e-4)
    assert r["mrel_pct_tem"] == pytest.approx(0.1087, abs=1e-4)
    assert r["mrel_requirement_trea"] == pytest.approx(0.226, abs=1e-3)
    # Surplus = capacity - requirement
    assert r["mrel_surplus_trea_pp"] == pytest.approx(0.3402 - 0.226, abs=1e-4)
