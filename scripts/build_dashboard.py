"""Rigenera la dashboard HTML statica per il CdA Banco BPM.

Questo script legge ``data/processed/facts.parquet`` (output di
``scripts/ingest.py``), calcola le metriche per il peer set CdA usando le
funzioni canoniche di ``core/metrics.py`` + ``core/cbr.py``, e produce un file
HTML self-contained con i dati embedded come ``const DATA={...};``.

Output: ``dashboard_mrel_cda_2025q4.html`` (alla root del progetto).

Template: ``scripts/dashboard_template/dashboard.html.tpl`` con placeholder
``__DASHBOARD_DATA__`` che viene sostituito dal JSON generato.

Universe scatter: ``scripts/dashboard_template/universe.json`` — set esteso di
banche (oltre il peer set CdA) usato per il grafico scatter "universe". Questi
sono punti raccolti manualmente da Pillar 3 PDF di banche EBA non incluse nella
pipeline standard (Nordea, ING Bank, Danske, KBC, ecc.).

Uso::

    python scripts/build_dashboard.py
    # opzionalmente:
    python scripts/build_dashboard.py --ref-date 2025-12-31

Test::

    python scripts/build_dashboard.py --validate-only
    # legge i dati ma non scrive l'HTML, utile per CI.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import pandas as pd

# Make project root importable when script is run directly.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.cbr import attach_cbr
from core.metrics import (
    creditor_rank_breakdown,
    km2_wide,
    tlac1_composition,
    tlac3_maturity,
)

# ── Costanti ────────────────────────────────────────────────────────────────

# Peer set CdA — Cluster 1 italiano (8 banche regolamentari)
CLUSTER1_LEIS = [
    "2W8N8UU78PMDQKZENC08",  # Intesa Sanpaolo
    "549300TRUWO2CD2G5692",  # UniCredit
    "815600E4E6DCD2D25E30",  # Banco BPM
    "J4CP7MHCXR8DAQMKIL78",  # MPS
    "LOO0AWXR8GF142JCO404",  # Cassa Centrale
    "N747OI7JINV7RUUH6190",  # BPER
    "NNVPP80YIZGEY2314M97",  # ICCREA
    "PSNL19R2RXX5U3QWHI44",  # Mediobanca
]

# Peer set CdA — Cluster 2 europeo (4 banche taglia simile)
CLUSTER2_LEIS = [
    "635400AKJBGNS5WNQL34",  # AIB Group
    "635400C8EK6DRI12LJ39",  # Bank of Ireland
    "A5GWLFH3KM7YV2SFQL84",  # Belfius Bank
    "SI5RG2M0WQQLZCXKRM20",  # Banco de Sabadell
]

BPM_LEI = "815600E4E6DCD2D25E30"

# Path
FACTS_PATH = ROOT / "data" / "processed" / "facts.parquet"
BANKS_PATH = ROOT / "data" / "processed" / "banks.parquet"
TEMPLATE_PATH = ROOT / "scripts" / "dashboard_template" / "dashboard.html.tpl"
UNIVERSE_PATH = ROOT / "scripts" / "dashboard_template" / "universe.json"
OUTPUT_PATH = ROOT / "dashboard_mrel_cda_2025q4.html"

DEFAULT_REF_DATE = "2025-12-31"


# ── Helper funzioni ──────────────────────────────────────────────────────────

def _drop_duplicate_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Removes duplicate columns by name, keeping the first occurrence.

    ``attach_cbr`` può duplicare colonne se chiamato due volte sulla stessa
    DataFrame — questa funzione protegge il risultato finale.
    """
    return df.loc[:, ~df.columns.duplicated()]


def _cluster_of(lei: str) -> str:
    if lei == BPM_LEI:
        return "c1"
    if lei in CLUSTER1_LEIS:
        return "c1"
    if lei in CLUSTER2_LEIS:
        return "c2"
    return "other"


def _bank_name(banks: pd.DataFrame, lei: str) -> str | None:
    row = banks[banks["entity_lei"] == lei]
    if row.empty:
        return None
    return str(row.iloc[0]["entity_name"])


def _round_or_none(value, ndigits: int = 4):
    """Round a numeric value to ``ndigits`` decimals; return None if NaN."""
    if pd.isna(value):
        return None
    return round(float(value), ndigits)


# ── Builder per ciascuna sezione del JSON ────────────────────────────────────

def build_km2_section(
    facts: pd.DataFrame,
    banks: pd.DataFrame,
    ref_date: pd.Timestamp,
    peer_leis: list[str],
) -> list[dict]:
    """Costruisce la sezione ``km2`` del JSON dashboard."""
    km2 = km2_wide(facts)
    km2 = attach_cbr(km2)
    km2 = _drop_duplicate_columns(km2)

    rows = []
    for lei in peer_leis:
        sub = km2[
            (km2["entity_lei"] == lei)
            & (km2["reference_date"] == ref_date)
        ]
        name = _bank_name(banks, lei) or lei
        cluster = _cluster_of(lei)

        if sub.empty:
            # Banca nel perimetro ma senza dati Q4 2025 — mette comunque entry vuota
            rows.append({
                "lei": lei,
                "name": name,
                "is_bpm": lei == BPM_LEI,
                "cluster": cluster,
                "mrel_pct_trea": None,
                "subord_pct_trea": None,
                "mrel_pct_tem": None,
                "mrel_requirement_trea_ex_cbr": None,
                "mrel_requirement_trea_with_cbr": None,
                "mrel_subord_requirement_trea_ex_cbr": None,
                "mrel_subord_requirement_trea_with_cbr": None,
                "mrel_requirement_tem": None,
                "mrel_subord_requirement_tem": None,
                "mrel_surplus_trea_ex_cbr_pp": None,
                "mrel_surplus_trea_with_cbr_pp": None,
                "subordination_ratio": None,
                "trea": None,
                "tem": None,
                "mrel_total_amount": None,
                "cet1_ratio": None,
                "total_capital_ratio": None,
                "leverage_ratio": None,
            })
            continue

        row = sub.iloc[0]
        rows.append({
            "lei": lei,
            "name": name,
            "is_bpm": lei == BPM_LEI,
            "cluster": cluster,
            "mrel_pct_trea": _round_or_none(row.get("mrel_pct_trea")),
            "subord_pct_trea": _round_or_none(row.get("subord_pct_trea")),
            "mrel_pct_tem": _round_or_none(row.get("mrel_pct_tem")),
            "mrel_requirement_trea_ex_cbr": _round_or_none(row.get("mrel_requirement_trea_ex_cbr")),
            "mrel_requirement_trea_with_cbr": _round_or_none(row.get("mrel_requirement_trea_with_cbr")),
            "mrel_subord_requirement_trea_ex_cbr": _round_or_none(row.get("mrel_subord_requirement_trea_ex_cbr")),
            "mrel_subord_requirement_trea_with_cbr": _round_or_none(row.get("mrel_subord_requirement_trea_with_cbr")),
            "mrel_requirement_tem": _round_or_none(row.get("mrel_requirement_tem")),
            "mrel_subord_requirement_tem": _round_or_none(row.get("mrel_subord_requirement_tem")),
            "mrel_surplus_trea_ex_cbr_pp": _round_or_none(row.get("mrel_surplus_trea_ex_cbr_pp")),
            "mrel_surplus_trea_with_cbr_pp": _round_or_none(row.get("mrel_surplus_trea_with_cbr_pp")),
            "subordination_ratio": _round_or_none(row.get("subordination_ratio"), ndigits=10),
            "trea": _round_or_none(row.get("trea"), ndigits=2),
            "tem": _round_or_none(row.get("tem"), ndigits=2),
            "mrel_total_amount": _round_or_none(row.get("mrel_total_amount"), ndigits=2),
            "cet1_ratio": _round_or_none(row.get("cet1_ratio"), ndigits=10),
            "total_capital_ratio": _round_or_none(row.get("total_capital_ratio"), ndigits=10),
            "leverage_ratio": _round_or_none(row.get("leverage_ratio"), ndigits=10),
        })
    return rows


def build_comp_section(
    facts: pd.DataFrame,
    banks: pd.DataFrame,
    ref_date: pd.Timestamp,
    peer_leis: list[str],
) -> list[dict]:
    """Costruisce la sezione ``comp`` (TLAC1 composition)."""
    comp = tlac1_composition(facts)
    rows = []
    for lei in peer_leis:
        sub = comp[
            (comp["entity_lei"] == lei)
            & (comp["reference_date"] == ref_date)
        ]
        if sub.empty:
            continue
        row = sub.iloc[0]
        rows.append({
            "lei": lei,
            "name": _bank_name(banks, lei) or lei,
            "is_bpm": lei == BPM_LEI,
            "cluster": _cluster_of(lei),
            "cet1": _round_or_none(row.get("cet1"), ndigits=2),
            "at1": _round_or_none(row.get("at1"), ndigits=2),
            "tier2": _round_or_none(row.get("tier2"), ndigits=2),
            "subord_el": _round_or_none(row.get("subord_eligible_liabilities"), ndigits=2),
            "senior_el": _round_or_none(row.get("senior_eligible_liabilities"), ndigits=2),
            "total": _round_or_none(row.get("total_stack"), ndigits=2),
        })
    return rows


def build_mat_section(
    facts: pd.DataFrame,
    banks: pd.DataFrame,
    ref_date: pd.Timestamp,
    peer_leis: list[str],
) -> list[dict]:
    """Costruisce la sezione ``mat`` (TLAC3 maturity ladder)."""
    mat = tlac3_maturity(facts)
    rows = []
    for lei in peer_leis:
        sub = mat[
            (mat["entity_lei"] == lei)
            & (mat["reference_date"] == ref_date)
        ]
        if sub.empty:
            continue
        row = sub.iloc[0]
        entry = {
            "lei": lei,
            "name": _bank_name(banks, lei) or lei,
            "is_bpm": lei == BPM_LEI,
            "cluster": _cluster_of(lei),
            "b1_2y": _round_or_none(row.get("maturity_1_to_2y"), ndigits=2),
            "b2_5y": _round_or_none(row.get("maturity_2_to_5y"), ndigits=2),
            "b5_10y": _round_or_none(row.get("maturity_5_to_10y"), ndigits=2),
            "b10y": _round_or_none(row.get("maturity_10y_plus"), ndigits=2),
            "perp": _round_or_none(row.get("maturity_perpetual"), ndigits=2),
            "total": _round_or_none(row.get("total_eligible"), ndigits=2),
            "s1_2y": _round_or_none(row.get("maturity_1_to_2y_share"), ndigits=10),
            "s2_5y": _round_or_none(row.get("maturity_2_to_5y_share"), ndigits=10),
            "s5_10y": _round_or_none(row.get("maturity_5_to_10y_share"), ndigits=10),
            "s10y": _round_or_none(row.get("maturity_10y_plus_share"), ndigits=10),
            "sperp": _round_or_none(row.get("maturity_perpetual_share"), ndigits=10),
        }
        rows.append(entry)
    return rows


def build_crd_section(
    facts: pd.DataFrame,
    banks: pd.DataFrame,
    ref_date: pd.Timestamp,
    peer_leis: list[str],
) -> list[dict]:
    """Costruisce la sezione ``crd`` (creditor ranking)."""
    crd = creditor_rank_breakdown(facts)
    rows = []
    for lei in peer_leis:
        sub = crd[
            (crd["entity_lei"] == lei)
            & (crd["reference_date"] == ref_date)
        ]
        if sub.empty:
            continue
        # Costruisco dict rank → amount (solo rank con valore > 0)
        ranks = {}
        for _, r in sub.iterrows():
            rank = r.get("rank")
            amt = r.get("value")
            if rank is None or pd.isna(rank) or amt is None or pd.isna(amt):
                continue
            if float(amt) > 0:
                ranks[str(int(rank))] = _round_or_none(float(amt), ndigits=2)
        if not ranks:
            continue
        rows.append({
            "lei": lei,
            "name": _bank_name(banks, lei) or lei,
            "is_bpm": lei == BPM_LEI,
            "cluster": _cluster_of(lei),
            "ranks": ranks,
        })
    return rows


def load_universe() -> list[dict]:
    """Carica l'universe array dal file JSON di template (mantenuto a mano)."""
    with open(UNIVERSE_PATH) as f:
        return json.load(f)


# ── Main ─────────────────────────────────────────────────────────────────────

def build_dashboard(ref_date_str: str = DEFAULT_REF_DATE, validate_only: bool = False) -> dict:
    """Costruisce il dict ``DATA`` per la dashboard. Restituisce il dict.

    Se ``validate_only=False`` scrive anche l'HTML finale.
    """
    ref_date = pd.Timestamp(ref_date_str)
    print(f"Building dashboard for ref_date = {ref_date_str}", file=sys.stderr)

    # Load data
    facts = pd.read_parquet(FACTS_PATH)
    banks = pd.read_parquet(BANKS_PATH)
    print(f"  Loaded {len(facts):,} facts, {len(banks)} banks", file=sys.stderr)

    # All peer LEIs (cluster 1 + cluster 2)
    peer_leis = CLUSTER1_LEIS + CLUSTER2_LEIS

    # Build each section
    km2_rows = build_km2_section(facts, banks, ref_date, peer_leis)
    comp_rows = build_comp_section(facts, banks, ref_date, peer_leis)
    mat_rows = build_mat_section(facts, banks, ref_date, peer_leis)
    crd_rows = build_crd_section(facts, banks, ref_date, peer_leis)
    universe = load_universe()

    print(f"  km2: {len(km2_rows)} rows", file=sys.stderr)
    print(f"  comp: {len(comp_rows)} rows", file=sys.stderr)
    print(f"  mat: {len(mat_rows)} rows", file=sys.stderr)
    print(f"  crd: {len(crd_rows)} rows", file=sys.stderr)
    print(f"  universe: {len(universe)} rows", file=sys.stderr)

    data = {
        "km2": km2_rows,
        "comp": comp_rows,
        "mat": mat_rows,
        "crd": crd_rows,
        "cluster1_leis": CLUSTER1_LEIS,
        "cluster2_leis": CLUSTER2_LEIS,
        "bpm_lei": BPM_LEI,
        "universe": universe,
    }

    if validate_only:
        print("Validate-only mode: not writing HTML.", file=sys.stderr)
        return data

    # Load template and substitute
    with open(TEMPLATE_PATH) as f:
        template = f.read()
    if "__DASHBOARD_DATA__" not in template:
        raise RuntimeError(
            f"Template {TEMPLATE_PATH} does not contain placeholder __DASHBOARD_DATA__"
        )
    data_json = json.dumps(data, separators=(",", ": "))
    html = template.replace("__DASHBOARD_DATA__", data_json)

    with open(OUTPUT_PATH, "w") as f:
        f.write(html)
    print(f"Written {OUTPUT_PATH} ({len(html):,} chars)", file=sys.stderr)

    return data


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--ref-date",
        default=DEFAULT_REF_DATE,
        help=f"Reference date in YYYY-MM-DD format (default: {DEFAULT_REF_DATE})",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate that data can be built, but don't write the HTML output.",
    )
    args = parser.parse_args()
    build_dashboard(ref_date_str=args.ref_date, validate_only=args.validate_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
