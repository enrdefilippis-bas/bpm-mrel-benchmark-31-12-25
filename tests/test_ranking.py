"""Tests for ranking and peer-summary helpers."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from core.ranking import peer_summary, rank_in_peer_set


def _metrics(values: dict[str, float]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"entity_lei": lei, "reference_date": pd.Timestamp("2025-12-31"), "metric": v}
            for lei, v in values.items()
        ]
    )


def test_rank_descending_puts_biggest_first():
    df = _metrics({"A": 0.40, "B": 0.30, "C": 0.35, "D": 0.25})
    r = rank_in_peer_set(df, "metric", ["A", "B", "C", "D"], "A", ascending=False)
    assert r.rank == 1
    assert r.total_with_data == 4
    assert r.total_selected == 4
    assert r.percentile == pytest.approx(100.0)
    assert r.value == pytest.approx(0.40)


def test_rank_middle_position_has_middle_percentile():
    df = _metrics({"A": 0.40, "B": 0.30, "C": 0.35, "D": 0.25})
    r = rank_in_peer_set(df, "metric", ["A", "B", "C", "D"], "C", ascending=False)
    assert r.rank == 2
    assert r.percentile == pytest.approx(100.0 * (4 - 2) / 3)


def test_rank_excludes_missing_data_but_preserves_selected_count():
    df = pd.DataFrame(
        [
            {"entity_lei": "A", "reference_date": pd.Timestamp("2025-12-31"), "metric": 0.30},
            {"entity_lei": "B", "reference_date": pd.Timestamp("2025-12-31"), "metric": np.nan},
            {"entity_lei": "C", "reference_date": pd.Timestamp("2025-12-31"), "metric": 0.40},
        ]
    )
    r = rank_in_peer_set(df, "metric", ["A", "B", "C"], "A", ascending=False)
    assert r.total_selected == 3
    assert r.total_with_data == 2
    assert r.rank == 2


def test_rank_returns_sentinel_when_target_missing():
    df = _metrics({"A": 0.40, "B": 0.30})
    r = rank_in_peer_set(df, "metric", ["A", "B", "X"], "X", ascending=False)
    assert r.rank == 0
    assert r.value is None


def test_peer_summary_reports_descriptive_stats():
    df = _metrics({"A": 0.40, "B": 0.30, "C": 0.35, "D": 0.25})
    s = peer_summary(df, "metric", ["A", "B", "C", "D"])
    assert s["n"] == 4
    assert s["median"] == pytest.approx(0.325, abs=1e-4)
    assert s["mean"] == pytest.approx(0.325, abs=1e-4)
    assert s["min"] == 0.25
    assert s["max"] == 0.40
    assert s["p25"] < s["p75"]


def test_peer_summary_on_empty_peer_set_is_all_nan_except_n():
    df = _metrics({"A": 0.40})
    s = peer_summary(df, "metric", ["X", "Y"])
    assert s["n"] == 0
    assert pd.isna(s["median"])
