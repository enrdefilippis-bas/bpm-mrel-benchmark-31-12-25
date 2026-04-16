"""Rank banks within a peer set or the full universe on a given metric."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class RankResult:
    """Position of a bank in a ranked peer list for a single metric."""

    entity_lei: str
    rank: int               # 1-based; rank 1 = highest value (or lowest if ascending)
    total_with_data: int    # denominator — banks in scope that actually have a value
    total_selected: int     # peer-set size as selected by the user
    percentile: float       # 0-100
    value: float | None


def rank_in_peer_set(
    metrics: pd.DataFrame,
    metric: str,
    peer_leis: list[str],
    target_lei: str,
    ascending: bool = False,
) -> RankResult:
    """Rank one bank within a peer set on one metric.

    `metrics` must be wide-format (one row per bank/date) filtered to the
    reference date of interest before calling. Missing values are excluded
    from the ranking — they still count toward `total_selected` but not
    `total_with_data`.
    """
    if metric not in metrics.columns:
        raise KeyError(f"metric {metric!r} not in metrics columns")
    peers = metrics[metrics["entity_lei"].isin(peer_leis)].copy()
    total_selected = len(peer_leis)

    with_data = peers.dropna(subset=[metric]).copy()
    total_with_data = len(with_data)
    if total_with_data == 0:
        return RankResult(target_lei, 0, 0, total_selected, float("nan"), None)

    with_data = with_data.sort_values(metric, ascending=ascending).reset_index(drop=True)
    with_data["rank"] = with_data.index + 1
    row = with_data[with_data["entity_lei"] == target_lei]
    if row.empty:
        return RankResult(target_lei, 0, total_with_data, total_selected, float("nan"), None)

    r = int(row["rank"].iloc[0])
    pct = 100.0 * (total_with_data - r) / max(total_with_data - 1, 1) if total_with_data > 1 else 100.0
    value = float(row[metric].iloc[0])
    return RankResult(target_lei, r, total_with_data, total_selected, pct, value)


def peer_summary(
    metrics: pd.DataFrame,
    metric: str,
    peer_leis: list[str],
) -> dict[str, float]:
    """Descriptive stats for a metric within a peer set — median, mean, p25, p75."""
    peers = metrics[metrics["entity_lei"].isin(peer_leis)][metric].dropna()
    if peers.empty:
        return {"n": 0.0, "median": float("nan"), "mean": float("nan"),
                "p25": float("nan"), "p75": float("nan"), "min": float("nan"), "max": float("nan")}
    return {
        "n": float(len(peers)),
        "median": float(peers.median()),
        "mean": float(peers.mean()),
        "p25": float(peers.quantile(0.25)),
        "p75": float(peers.quantile(0.75)),
        "min": float(peers.min()),
        "max": float(peers.max()),
    }
