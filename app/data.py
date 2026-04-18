"""Runtime data access for the Dash app.

Loads the ingested parquet files once at startup into module-level caches.
Keeps the UI layer free of pandas plumbing and avoids re-reading the
parquet on every callback.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pandas as pd

from core.metrics import (
    attach_bank_meta,
    cet1_ratio,
    km2_wide,
    leverage_ratio,
    t1_capital_ratio,
    total_assets,
    total_capital_ratio,
)
from core.peers import ALL_PEER_SETS, BPM_LEI, PeerSet, resolve_peer_set
from core.schema import empty_facts

ROOT = Path(__file__).resolve().parent.parent
PROCESSED = ROOT / "data" / "processed"
FACTS_PATH = PROCESSED / "facts.parquet"
BANKS_PATH = PROCESSED / "banks.parquet"


@lru_cache(maxsize=1)
def load_facts() -> pd.DataFrame:
    """Load the long-format facts table, or return an empty typed frame."""
    if not FACTS_PATH.exists():
        return empty_facts()
    return pd.read_parquet(FACTS_PATH)


@lru_cache(maxsize=1)
def load_banks() -> pd.DataFrame:
    """Load the bank dimension table."""
    if not BANKS_PATH.exists():
        return pd.DataFrame(columns=["entity_lei", "entity_name", "country"])
    return pd.read_parquet(BANKS_PATH)


@lru_cache(maxsize=1)
def load_km2() -> pd.DataFrame:
    """Wide KM2 metrics enriched with bank display name + country."""
    facts = load_facts()
    km2 = km2_wide(facts)

    # Add new solvency metrics
    ta = total_assets(facts)
    c1r = cet1_ratio(facts)
    tcr = total_capital_ratio(facts)
    lr = leverage_ratio(facts)

    # Merge all metrics
    for df in [ta, c1r, tcr, lr]:
        if not df.empty:
            km2 = km2.merge(df, on=["entity_lei", "reference_date"], how="left")

    return attach_bank_meta(km2, load_banks())


def available_reference_dates() -> list[pd.Timestamp]:
    """Sorted list of quarter-end reference dates present in the data."""
    facts = load_facts()
    if facts.empty:
        return []
    return sorted(pd.unique(facts["reference_date"]))


def reference_date_options() -> list[dict]:
    """Dropdown options — most recent first."""
    dates = available_reference_dates()
    return [
        {"label": pd.Timestamp(d).strftime("%Y-%m-%d"), "value": pd.Timestamp(d).isoformat()}
        for d in reversed(dates)
    ]


def latest_reference_date() -> pd.Timestamp | None:
    dates = available_reference_dates()
    return pd.Timestamp(dates[-1]) if dates else None


def peer_set_options() -> list[dict]:
    """Dropdown options for the peer-set selector."""
    return [{"label": ps.label, "value": ps.key} for ps in ALL_PEER_SETS]


def peer_set_by_key(key: str) -> PeerSet:
    for ps in ALL_PEER_SETS:
        if ps.key == key:
            return ps
    return ALL_PEER_SETS[0]


def resolve_peers(key: str) -> list[str]:
    """Return the concrete LEI list for a peer-set key."""
    peer_set = peer_set_by_key(key)
    # For dynamic peer sets (like EU_OSII_SIMILAR_SIZE), also pass facts
    if peer_set.key == "eu_osii_similar_size":
        return resolve_peer_set(peer_set, load_banks(), facts=load_facts())
    return resolve_peer_set(peer_set, load_banks())


def peer_display_names(leis: list[str]) -> dict[str, str]:
    """Map LEI → display name (fallbacks to LEI if unknown)."""
    banks = load_banks()
    if banks.empty:
        return {lei: lei for lei in leis}
    m = banks.set_index("entity_lei")["entity_name"].to_dict()
    return {lei: m.get(lei, lei) for lei in leis}


def data_is_loaded() -> bool:
    """True if both parquet files are available."""
    return FACTS_PATH.exists() and BANKS_PATH.exists()


# Convenience
BPM = BPM_LEI
