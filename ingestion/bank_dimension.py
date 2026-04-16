"""Build the banks dimension table from the canonical facts.

One row per LEI; latest known name + country. Peer-set membership flags
are derived at runtime by `core.peers.resolve_peer_set` rather than
being baked in here, so changing the peer definitions does not require
a re-ingest.
"""
from __future__ import annotations

import pandas as pd

from core.peers import ALL_PEER_SETS, resolve_peer_set


def build_bank_dimension(facts: pd.DataFrame) -> pd.DataFrame:
    """Return one row per bank with the latest known name + country."""
    if facts.empty:
        return pd.DataFrame(
            columns=[
                "entity_lei",
                "entity_name",
                "country",
                *(f"in_{ps.key}" for ps in ALL_PEER_SETS),
            ]
        )

    latest = (
        facts.sort_values("reference_date")
        .groupby("entity_lei", as_index=False)
        .agg({"entity_name": "last", "country": "last"})
        .sort_values("entity_name")
        .reset_index(drop=True)
    )

    # Peer-set membership columns — each is a boolean per bank.
    for ps in ALL_PEER_SETS:
        leis = set(resolve_peer_set(ps, latest))
        latest[f"in_{ps.key}"] = latest["entity_lei"].isin(leis)

    return latest
