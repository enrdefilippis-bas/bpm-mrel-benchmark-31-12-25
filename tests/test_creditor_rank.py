"""Tests for the creditor-rank (TLAC3 / TLAC3b) derivation."""
from __future__ import annotations

import pandas as pd
import pytest

from core.metrics import CREDITOR_RANK_SOURCES, creditor_rank_breakdown
from core.schema import Source, Template, UnitType


def _fact(lei, template, row, col, value, *, open_key="",
          date="2025-12-31") -> dict:
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


RANK = "Ranking in insolvency = Rank {n} - Ranking in insolvency (master scale)"


def test_creditor_rank_resolution_extracts_per_rank_values():
    rows = [
        # Per-rank MREL-eligible amounts (col 0010).
        _fact("LEI1", Template.TLAC3.value, "0050", "0010", 12.0e9,
              open_key=RANK.format(n=1)),
        _fact("LEI1", Template.TLAC3.value, "0050", "0010", 5.0e9,
              open_key=RANK.format(n=5)),
        _fact("LEI1", Template.TLAC3.value, "0050", "0010", 0.3e9,
              open_key=RANK.format(n=6)),
        # Sum-of-ranks aggregate at col 0050 must not be picked up.
        _fact("LEI1", Template.TLAC3.value, "0050", "0050", 17.3e9),
        # Another row code at col 0010 with a rank open_key must not be
        # picked up — we want row 0050 only.
        _fact("LEI1", Template.TLAC3.value, "0040", "0010", 99.0e9,
              open_key=RANK.format(n=1)),
    ]
    out = creditor_rank_breakdown(pd.DataFrame(rows), scope="resolution")
    assert len(out) == 3
    assert list(out["rank"]) == [1, 5, 6]
    assert out.set_index("rank")["value"].to_dict() == {
        1: pytest.approx(12.0e9),
        5: pytest.approx(5.0e9),
        6: pytest.approx(0.3e9),
    }


def test_creditor_rank_non_resolution_uses_k98_row_0020():
    rows = [
        _fact("LEI1", Template.TLAC3B.value, "0020", "0010", 3.0e9,
              open_key=RANK.format(n=1)),
        _fact("LEI1", Template.TLAC3B.value, "0020", "0010", 1.2e9,
              open_key=RANK.format(n=3)),
        # K_97 row must NOT be picked up when scope is non_resolution.
        _fact("LEI1", Template.TLAC3.value, "0050", "0010", 99.0e9,
              open_key=RANK.format(n=1)),
    ]
    out = creditor_rank_breakdown(pd.DataFrame(rows), scope="non_resolution")
    assert len(out) == 2
    assert set(out["rank"]) == {1, 3}
    assert out["value"].sum() == pytest.approx(4.2e9)


def test_creditor_rank_empty_facts_returns_empty_frame():
    out = creditor_rank_breakdown(pd.DataFrame(columns=[
        "entity_lei", "reference_date", "template",
        "row_code", "col_code", "open_key", "value",
    ]))
    assert out.empty
    assert list(out.columns) == ["entity_lei", "reference_date", "rank", "value"]


def test_creditor_rank_scope_registry_covers_resolution_and_non_resolution():
    assert set(CREDITOR_RANK_SOURCES) == {"resolution", "non_resolution"}
    assert CREDITOR_RANK_SOURCES["resolution"][0] == Template.TLAC3.value
    assert CREDITOR_RANK_SOURCES["non_resolution"][0] == Template.TLAC3B.value


def test_creditor_rank_rejects_unknown_scope():
    with pytest.raises(ValueError, match="Unknown creditor-rank scope"):
        creditor_rank_breakdown(pd.DataFrame(), scope="bogus")
