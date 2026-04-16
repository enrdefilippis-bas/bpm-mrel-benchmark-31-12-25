"""Tests for TLAC1 composition + TLAC3 maturity derivations."""
from __future__ import annotations

import pandas as pd
import pytest

from core.metrics import (
    TLAC1_COMPOSITION_CLASSES,
    TLAC3_MATURITY_BUCKETS,
    tlac1_composition,
    tlac3_maturity,
)
from core.schema import Source, Template, UnitType


def _fact(lei: str, template: str, row: str, col: str, value: float,
          date: str = "2025-12-31", open_key: str = "") -> dict:
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
        "open_key": open_key,
        "raw_value": value,
        "value": value,
        "unit": UnitType.AMOUNT_EUR.value,
        "source": Source.EBA_EXPORT.value,
        "ingested_at": pd.Timestamp.now("UTC").tz_localize(None),
    }


def test_tlac1_composition_sums_subordinated_eligible_liabilities():
    """Subord class = sum of rows 0100, 0110, 0120, 0130."""
    rows = [
        _fact("LEI1", Template.TLAC1.value, "0010", "0010", 9.0e9),   # CET1
        _fact("LEI1", Template.TLAC1.value, "0020", "0010", 1.0e9),   # AT1
        _fact("LEI1", Template.TLAC1.value, "0060", "0010", 2.0e9),   # T2
        _fact("LEI1", Template.TLAC1.value, "0100", "0010", 1.5e9),   # subord — own
        _fact("LEI1", Template.TLAC1.value, "0110", "0010", 0.5e9),   # subord — intra
        _fact("LEI1", Template.TLAC1.value, "0120", "0010", 0.2e9),   # subord — grandfathered
        _fact("LEI1", Template.TLAC1.value, "0130", "0010", 0.1e9),   # subord — T2-residual
        _fact("LEI1", Template.TLAC1.value, "0140", "0010", 10.0e9),  # senior
        _fact("LEI1", Template.TLAC1.value, "0150", "0010", 2.0e9),   # senior — grandfathered
        _fact("LEI1", Template.TLAC1.value, "0160", "0010", 0.0),     # senior — post-cap
    ]
    comp = tlac1_composition(pd.DataFrame(rows))
    assert len(comp) == 1
    r = comp.iloc[0]
    assert r["cet1"] == pytest.approx(9.0e9)
    assert r["at1"] == pytest.approx(1.0e9)
    assert r["tier2"] == pytest.approx(2.0e9)
    assert r["subord_eligible_liabilities"] == pytest.approx(2.3e9)
    assert r["senior_eligible_liabilities"] == pytest.approx(12.0e9)
    assert r["total_stack"] == pytest.approx(9.0e9 + 1.0e9 + 2.0e9 + 2.3e9 + 12.0e9)


def test_tlac1_composition_empty_facts_returns_empty():
    comp = tlac1_composition(pd.DataFrame(columns=["entity_lei", "reference_date",
                                                    "template", "row_code",
                                                    "col_code", "value"]))
    assert comp.empty
    for cls in TLAC1_COMPOSITION_CLASSES:
        assert cls in comp.columns


def test_tlac3_maturity_shares_sum_to_one():
    """Bucket shares divided by total_eligible sum to 1.0."""
    total = 1000.0
    rows = [
        _fact("LEI1", Template.TLAC3.value, "0050", "0050", total),
        _fact("LEI1", Template.TLAC3.value, "0060", "0050", 100.0),   # 1-2y  → 10%
        _fact("LEI1", Template.TLAC3.value, "0070", "0050", 300.0),   # 2-5y  → 30%
        _fact("LEI1", Template.TLAC3.value, "0080", "0050", 200.0),   # 5-10y → 20%
        _fact("LEI1", Template.TLAC3.value, "0090", "0050", 100.0),   # 10y+  → 10%
        _fact("LEI1", Template.TLAC3.value, "0100", "0050", 300.0),   # perp  → 30%
    ]
    mat = tlac3_maturity(pd.DataFrame(rows))
    assert len(mat) == 1
    r = mat.iloc[0]
    shares = [r[f"{k}_share"] for k in TLAC3_MATURITY_BUCKETS]
    assert sum(shares) == pytest.approx(1.0)
    assert r["maturity_1_to_2y_share"] == pytest.approx(0.10)
    assert r["under_2y_share"] == pytest.approx(0.10)


def test_tlac3_maturity_handles_zero_total_without_infinity():
    rows = [
        _fact("LEI1", Template.TLAC3.value, "0050", "0050", 0.0),
        _fact("LEI1", Template.TLAC3.value, "0060", "0050", 0.0),
    ]
    mat = tlac3_maturity(pd.DataFrame(rows))
    assert pd.isna(mat["maturity_1_to_2y_share"].iloc[0])