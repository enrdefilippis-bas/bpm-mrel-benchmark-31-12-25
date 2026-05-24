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


ITALIAN_OSII_RESOLUTION = PeerSet(
    key="italian_osii_resolution",
    label="Italian O-SIIs under resolution",
    description="The 7 Italian O-SIIs subject to resolution planning.",
    # Explicit LEI whitelist for the 7 Italian O-SIIs
    # (No name_hints to avoid matching foreign subsidiaries like UniCredit Bank Austria/GmbH)
    leis=(
        "815600E4E6DCD2D25E30",  # Banco BPM
        "549300TRUWO2CD2G5692",  # UniCredit S.p.A. (parent, Italian)
        "2W8N8UU78PMDQKZENC08",  # Intesa Sanpaolo S.p.A.
        "J4CP7MHCXR8DAQMKIL78",  # Banca Monte dei Paschi di Siena S.p.A.
        "N747OI7JINV7RUUH6190",  # BPER Banca S.p.A.
        "PSNL19R2RXX5U3QWHI44",  # Mediobanca - Banca di Credito Finanziario S.p.A.
        "NNVPP80YIZGEY2314M97",  # ICCREA BANCA S.P.A.
    ),
)


# =============================================================================
# CdA presentation peer sets (May 2026) — frozen, methodology approved by
# Enrico. Both are LEI whitelists (stable, no name-hint drift).
# =============================================================================

# Cluster 1 — Italian resolution-entity peers for the CdA presentation.
# Selected on: (i) Italian parent group, (ii) resolution entity standalone
# (NOT a subsidiary of a foreign group — BNL/Crédit Agricole Italia/Mediobanca
# Premier excluded), (iii) Pillar 3 with full EU KM2 + TLAC1 + TLAC3 templates
# (ground-truth verified on BPM, MPS Q4 2024). Includes MPS even though it
# is NOT on the 2024 O-SII list, because it publishes a full MREL Pillar 3
# and is the natural domestic comparator for BPM.
ITALIAN_PEERS_CDA = PeerSet(
    key="italian_peers_cda",
    label="Italian peers — CdA cluster 1",
    description=(
        "8 Italian resolution-entity peers with full MREL disclosure. "
        "Includes MPS (not on 2024 O-SII list but full MREL filer). "
        "Excludes BNL/CAI/Mediobanca Premier (subsidiaries of cross-border groups)."
    ),
    leis=(
        "815600E4E6DCD2D25E30",  # Banco BPM (anchor)
        "549300TRUWO2CD2G5692",  # UniCredit S.p.A.
        "2W8N8UU78PMDQKZENC08",  # Intesa Sanpaolo S.p.A.
        "J4CP7MHCXR8DAQMKIL78",  # Banca Monte dei Paschi di Siena S.p.A.
        "N747OI7JINV7RUUH6190",  # BPER Banca S.p.A.
        "PSNL19R2RXX5U3QWHI44",  # Mediobanca - Banca di Credito Finanziario S.p.A.
        "NNVPP80YIZGEY2314M97",  # ICCREA Banca S.p.A.
        "LOO0AWXR8GF142JCO404",  # Cassa Centrale Banca
    ),
)


# Cluster 2 — EU peers of comparable size (130-300B TEM ≈ BPM 204B), Eurozone
# only, commercial-retail business model. Excludes:
# - subsidiaries (ING Belgie -> ING Groep NL)
# - non-Eurozone (DNB Norway, Swedbank Sweden, PKO Poland)
# - universal/bancassurance too large (KBC 380B)
# - too small (Bankinter 124B < 130B floor)
EU_PEERS_CDA = PeerSet(
    key="eu_peers_cda",
    label="EU peers — CdA cluster 2 (similar size, Eurozone)",
    description=(
        "4 EU resolution-entity peers of comparable size (130-300B TEM) "
        "in the Eurozone with commercial-retail business model."
    ),
    leis=(
        "635400C8EK6DRI12LJ39",  # Bank of Ireland Group plc (IE, 141B)
        "635400AKJBGNS5WNQL34",  # AIB Group plc (IE, 149B)
        "A5GWLFH3KM7YV2SFQL84",  # Belfius Bank (BE, 191B)
        "SI5RG2M0WQQLZCXKRM20",  # Banco de Sabadell, S.A. (ES, 246B)
    ),
)


def resolve_eu_osii_similar_size(banks: "pandas.DataFrame") -> list[str]:
    """Dynamically resolve EU O-SIIs with similar size (150-300B TEM).

    Filters banks.parquet for entities whose Q4-2025 TEM (K_90.01 row 0060
    col 0010) is between 150,000 and 300,000 EUR millions. Returns sorted LEIs.
    """
    if banks.empty:
        return []

    # Import here to avoid circular imports
    from core.schema import Template

    # We need to access the facts to get TEM values
    # But this function receives only the banks dimension table
    # The caller (resolve_peer_set) will need to pass facts or we compute at UI level
    # For now, return an empty set; the actual implementation happens in UI/pages
    return []


EU_OSII_SIMILAR_SIZE = PeerSet(
    key="eu_osii_similar_size",
    label="EU peers – similar size (150–300B TEM)",
    description="EU banks with Q4-2025 total assets between EUR 150-300 billion.",
    # This set is dynamically resolved at runtime based on TEM data
)


ALL_PEER_SETS: tuple[PeerSet, ...] = (
    ITALIAN_PEERS_CDA,            # Cluster 1 — primary peer set for CdA narrative
    EU_PEERS_CDA,                 # Cluster 2 — EU peers of similar size for CdA
    DEFAULT_BPM_PEERS,
    ITALIAN_SIS,
    G_SIBS,
    EU_MID_CAP,
    ITALIAN_OSII_RESOLUTION,
    EU_OSII_SIMILAR_SIZE,
)


def resolve_peer_set(
    peer_set: PeerSet,
    banks: "pandas.DataFrame",
    facts: "pandas.DataFrame | None" = None,
) -> list[str]:
    """Map a PeerSet to concrete LEIs present in a banks dimension table.

    `banks` must have columns `entity_lei` and `entity_name`. Returns the
    sorted list of LEIs that match by LEI or case-insensitive substring
    on `entity_name`. Missing hints silently drop — visible in the UI via
    the "N of M selected have data" counter.

    For the special EU_OSII_SIMILAR_SIZE peer set, also requires `facts`
    to filter by TEM range (150-300B EUR).
    """
    import pandas as pd

    if banks.empty:
        return []

    # Special handling for EU_OSII_SIMILAR_SIZE: filter by TEM range
    if peer_set.key == "eu_osii_similar_size":
        if facts is None or facts.empty:
            return []
        # Get Q4-2025 TEM values
        from core.schema import Template

        q4_2025 = pd.Timestamp("2025-12-31")
        tem_mask = (
            (facts["template"] == Template.KM2.value)
            & (facts["row_code"] == "0060")
            & (facts["col_code"] == "0010")
            & (facts["reference_date"] == q4_2025)
        )
        tem_data = facts.loc[tem_mask, ["entity_lei", "value"]].copy()

        if tem_data.empty:
            return []

        # Filter to banks with TEM between 150B and 300B EUR
        # Values are in EUR (not millions), so 150B = 150_000_000_000
        in_range = tem_data[
            (tem_data["value"] >= 150_000_000_000) & (tem_data["value"] <= 300_000_000_000)
        ]["entity_lei"].tolist()

        # Filter to banks present in the banks dimension
        present = set(banks["entity_lei"].astype(str))
        return sorted(set(in_range) & present)

    matched: set[str] = set(peer_set.leis)
    if peer_set.name_hints:
        names = banks["entity_name"].astype(str)
        for hint in peer_set.name_hints:
            hits = banks.loc[names.str.contains(hint, case=False, regex=False), "entity_lei"]
            matched.update(hits.tolist())
    # Filter to LEIs actually present in the dim table.
    present = set(banks["entity_lei"].astype(str))
    return sorted(matched & present)
