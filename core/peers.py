"""Peer-set definitions anchored on Banco BPM.

The tool uses a tiered peer model:
- a `DEFAULT` tight peer set for the home scorecard and narrative pages;
- preset peer groups the user can switch to (Italian SIs, EU mid-cap, G-SIBs);
- plus full-universe selection on the outlier explorer page.

Peer identity uses Legal Entity Identifiers (LEI) — stable across filings and
renames. Display names may change between releases; LEIs do not.
"""
from __future__ import annotations

from dataclasses import dataclass, field


# Anchor bank: Banco BPM S.p.A.
BPM_LEI = "815600E4E6DCD2D25E30"  # filled in by tests at runtime if unknown


@dataclass(frozen=True)
class PeerSet:
    """A named group of banks identified by LEI."""

    key: str
    label: str
    description: str
    leis: tuple[str, ...] = field(default_factory=tuple)
    name_hints: tuple[str, ...] = field(default_factory=tuple)  # substrings to resolve by name


# We resolve peer sets by LEI *or* by substring match on bank name at runtime
# (`resolve_peer_set` below), because LEIs for some banks only become known
# after the first ingestion. Missing banks simply don't appear in the set.

DEFAULT_BPM_PEERS = PeerSet(
    key="bpm_default",
    label="BPM default peers",
    description=(
        "Banco BPM against its direct Italian competitors and a tight ring of "
        "comparable-size European banks."
    ),
    name_hints=(
        "BANCO BPM",
        "Intesa Sanpaolo",                   # via PDF ingestion
        "UniCredit S.p.A",                   # via PDF ingestion (parent)
        "BPER Banca",
        "Banca Monte dei Paschi",
        "CREDITO EMILIANO",
        "Mediobanca - Banca di Credito",
        "Banco de Sabadell",
        "CaixaBank",
        "Bankinter",
        "Banco Santander",
        "Banco Bilbao Vizcaya Argentaria",   # via PDF ingestion
        "BNP Paribas",
        "Groupe BPCE",
        "Crédit Agricole S.A",               # via PDF ingestion
        "Société Générale",                  # via PDF ingestion
        "ING Groep",
        "Coöperatieve Rabobank",
        "ABN AMRO Bank",
        "KBC Groupe",
        "Erste Bank",
        "COMMERZBANK",
        "DEUTSCHE BANK",
        "AIB Group",
        "Bank of Ireland",
    ),
)


ITALIAN_SIS = PeerSet(
    key="italian_sis",
    label="Italian significant institutions",
    description="Italian banks that file the EBA Pillar 3 MREL/TLAC disclosure.",
    name_hints=(
        "BANCO BPM",
        "Intesa Sanpaolo",
        "UniCredit S.p.A",
        "BPER",
        "Banca Monte dei Paschi",
        "CREDITO EMILIANO",
        "Mediobanca",
        "FINECOBANK",
        "ICCREA",
        "CASSA CENTRALE",
        "CRÉDIT AGRICOLE ITALIA",
        "BANCA MEDIOLANUM",
        "BANCA POPOLARE DI SONDRIO",
        "BANCA NAZIONALE DEL LAVORO",
    ),
)


G_SIBS = PeerSet(
    key="g_sibs",
    label="European G-SIBs",
    description="EU global systemically important banks.",
    name_hints=(
        "BNP Paribas",
        "Groupe BPCE",
        "Crédit Agricole S.A",
        "Société Générale",
        "DEUTSCHE BANK",
        "ING Groep",
        "Banco Santander",
        "Banco Bilbao Vizcaya Argentaria",
        "UniCredit S.p.A",
        "Intesa Sanpaolo",
    ),
)


EU_MID_CAP = PeerSet(
    key="eu_mid_cap",
    label="EU mid-cap banks",
    description="EU banks of comparable balance-sheet size to Banco BPM.",
    name_hints=(
        "BANCO BPM",
        "BPER",
        "Banca Monte dei Paschi",
        "Banco de Sabadell",
        "Bankinter",
        "CaixaBank",
        "Ibercaja Banco",
        "Kutxabank",
        "COMMERZBANK",
        "KBC Groupe",
        "Erste Bank",
        "Belfius Bank",
        "AIB Group",
        "Bank of Ireland",
        "Aktia Bank",
    ),
)


ALL_PEER_SETS: tuple[PeerSet, ...] = (
    DEFAULT_BPM_PEERS,
    ITALIAN_SIS,
    G_SIBS,
    EU_MID_CAP,
)


def resolve_peer_set(peer_set: PeerSet, banks: "pandas.DataFrame") -> list[str]:
    """Map a PeerSet to concrete LEIs present in a banks dimension table.

    `banks` must have columns `entity_lei` and `entity_name`. Returns the
    sorted list of LEIs that match by LEI or case-insensitive substring
    on `entity_name`. Missing hints silently drop — visible in the UI via
    the "N of M selected have data" counter.
    """
    import pandas as pd

    if banks.empty:
        return []

    matched: set[str] = set(peer_set.leis)
    if peer_set.name_hints:
        names = banks["entity_name"].astype(str)
        for hint in peer_set.name_hints:
            hits = banks.loc[names.str.contains(hint, case=False, regex=False), "entity_lei"]
            matched.update(hits.tolist())
    # Filter to LEIs actually present in the dim table.
    present = set(banks["entity_lei"].astype(str))
    return sorted(matched & present)
