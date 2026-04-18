"""Derive analyst-facing metrics from the canonical facts table.

Each function takes the full facts DataFrame and returns a wide
per-(bank, ref-date) table keyed by `entity_lei` + `reference_date`.
Callers combine columns for the various pages.
"""
from __future__ import annotations

import re

import pandas as pd

from core.captions import METRIC_CAPTIONS
from core.schema import Template


def _pick(
    facts: pd.DataFrame,
    template: str,
    row_code: str,
    col_code: str = "0010",
) -> pd.DataFrame:
    """Extract a single cell per (bank, ref-date) from the facts table."""
    mask = (
        (facts["template"] == template)
        & (facts["row_code"] == row_code)
        & (facts["col_code"] == col_code)
    )
    sel = facts.loc[mask, ["entity_lei", "reference_date", "value"]]
    return sel.drop_duplicates(["entity_lei", "reference_date"])


def km2_wide(facts: pd.DataFrame) -> pd.DataFrame:
    """Wide KM2 view — one row per (bank, ref-date), core KM2 cells as columns."""
    cells = {
        "mrel_total_amount": ("0010", "0010"),
        "trea": ("0030", "0010"),
        "tem": ("0060", "0010"),
        "mrel_pct_trea": ("0040", "0010"),
        "subord_pct_trea": ("0050", "0010"),
        "mrel_pct_tem": ("0070", "0010"),
        "mrel_requirement_trea": ("0120", "0010"),
        "mrel_subord_requirement_trea": ("0130", "0010"),
        "mrel_requirement_tem": ("0140", "0010"),
        "mrel_subord_requirement_tem": ("0150", "0010"),
    }
    tpl = Template.KM2.value
    out: pd.DataFrame | None = None
    for metric, (row, col) in cells.items():
        slice_ = _pick(facts, tpl, row, col).rename(columns={"value": metric})
        out = slice_ if out is None else out.merge(
            slice_, on=["entity_lei", "reference_date"], how="outer"
        )

    assert out is not None
    out = out.sort_values(["entity_lei", "reference_date"]).reset_index(drop=True)
    out["mrel_surplus_trea_pp"] = out["mrel_pct_trea"] - out["mrel_requirement_trea"]
    out["mrel_surplus_tem_pp"] = out["mrel_pct_tem"] - out["mrel_requirement_tem"]

    # Derived subordination ratio — defensive against zero denominators.
    import numpy as np
    out["subordination_ratio"] = (
        out["subord_pct_trea"] / out["mrel_pct_trea"].replace(0, np.nan)
    )

    return out


def attach_bank_meta(metrics: pd.DataFrame, banks: pd.DataFrame) -> pd.DataFrame:
    """Left-join bank display name + country onto a metrics frame."""
    if metrics.empty:
        return metrics
    meta = banks[["entity_lei", "entity_name", "country"]]
    return metrics.merge(meta, on="entity_lei", how="left")


def available_metric_keys() -> list[str]:
    """Metric keys that the UI can plot — keeps captions in sync."""
    return list(METRIC_CAPTIONS)


# ---- New solvency and capital metrics ----

def total_assets(facts: pd.DataFrame) -> pd.DataFrame:
    """Total assets (TEM) from K_90.01 row 0060 col 0010.

    Returns EUR (absolute value, as reported in the EBA export).
    """
    return _pick(facts, Template.KM2.value, "0060", "0010").rename(
        columns={"value": "total_assets"}
    )


def cet1_ratio(facts: pd.DataFrame) -> pd.DataFrame:
    """CET1 ratio from K_91.00.

    Attempts to find the row with "CET1" and "ratio/percentage" in the name.
    Falls back to row 0330 if the search fails. Values should be in the
    range 0.10-0.25 for typical banks.
    """
    tpl = Template.TLAC1.value

    # Search for a row containing both "CET1" and "ratio" or "percentage"
    # First, look for rows that have both CET1 AND ratio/percentage in the name
    cet1_mask = (
        (facts["template"] == tpl)
        & (facts["col_code"] == "0010")
        & facts["row_name"].fillna("").str.contains("CET1", case=False, regex=False)
    )
    cet1_candidates = facts.loc[cet1_mask, ["row_code", "row_name"]].drop_duplicates()

    # Filter to rows that explicitly mention ratio or percentage
    ratio_candidates = cet1_candidates[
        cet1_candidates["row_name"].str.contains("ratio|percentage", case=False, regex=True)
    ]

    if not ratio_candidates.empty:
        # Pick the first match (usually the main CET1 ratio)
        row_code = ratio_candidates.iloc[0]["row_code"]
    else:
        # Fallback to row 0330 (the traditional location)
        row_code = "0330"

    return _pick(facts, tpl, row_code, "0010").rename(
        columns={"value": "cet1_ratio"}
    )


def t1_capital_ratio(facts: pd.DataFrame) -> pd.DataFrame:
    """Tier 1 capital ratio from K_91.00.

    Searches for a row with "Tier 1" and "ratio/percentage" in the name.
    If not found, computes Tier1 / TREA ratio instead.
    """
    tpl = Template.TLAC1.value

    # Search for Tier 1 ratio row
    mask = (
        (facts["template"] == tpl)
        & (facts["col_code"] == "0010")
        & facts["row_name"].fillna("").str.contains("Tier 1|T1", case=False, regex=False)
    )
    candidates = facts.loc[mask, ["row_code", "row_name"]].drop_duplicates()

    # Prefer rows with "ratio" or "percentage"
    ratio_candidates = candidates[
        candidates["row_name"].str.contains("ratio|percentage", case=False, regex=True)
    ]

    if not ratio_candidates.empty:
        row_code = ratio_candidates.iloc[0]["row_code"]
        return _pick(facts, tpl, row_code, "0010").rename(
            columns={"value": "t1_capital_ratio"}
        )

    # Fallback: compute Tier1 / TREA
    # Tier 1 capital is typically row 0020 in K_91.00
    tier1 = _pick(facts, tpl, "0020", "0010").rename(columns={"value": "tier1"})
    trea = _pick(facts, Template.KM2.value, "0030", "0010").rename(columns={"value": "trea"})

    if tier1.empty or trea.empty:
        return pd.DataFrame(columns=["entity_lei", "reference_date", "t1_capital_ratio"])

    merged = tier1.merge(trea, on=["entity_lei", "reference_date"], how="inner")
    merged["t1_capital_ratio"] = merged["tier1"] / merged["trea"].replace(0, pd.NA)
    return merged[["entity_lei", "reference_date", "t1_capital_ratio"]]


def total_capital_ratio(facts: pd.DataFrame) -> pd.DataFrame:
    """Total capital ratio from K_91.00.

    Searches for a row with "Total capital" and "ratio/percentage" in the name.
    If not found, computes (CET1 + AT1 + T2) / TREA instead.
    """
    tpl = Template.TLAC1.value

    # Search for total capital ratio row
    mask = (
        (facts["template"] == tpl)
        & (facts["col_code"] == "0010")
        & facts["row_name"].fillna("").str.contains("total capital", case=False, regex=False)
    )
    candidates = facts.loc[mask, ["row_code", "row_name"]].drop_duplicates()

    # Prefer rows with "ratio" or "percentage"
    ratio_candidates = candidates[
        candidates["row_name"].str.contains("ratio|percentage", case=False, regex=True)
    ]

    if not ratio_candidates.empty:
        row_code = ratio_candidates.iloc[0]["row_code"]
        return _pick(facts, tpl, row_code, "0010").rename(
            columns={"value": "total_capital_ratio"}
        )

    # Fallback: compute (CET1 + AT1 + T2) / TREA
    cet1_amt = _pick(facts, tpl, "0010", "0010").rename(columns={"value": "cet1_amt"})
    at1_amt = _pick(facts, tpl, "0020", "0010").rename(columns={"value": "at1_amt"})
    t2_amt = _pick(facts, tpl, "0060", "0010").rename(columns={"value": "t2_amt"})
    trea = _pick(facts, Template.KM2.value, "0030", "0010").rename(columns={"value": "trea"})

    if cet1_amt.empty or trea.empty:
        return pd.DataFrame(columns=["entity_lei", "reference_date", "total_capital_ratio"])

    # Merge all components
    merged = cet1_amt
    for df, col in [(at1_amt, "at1_amt"), (t2_amt, "t2_amt"), (trea, "trea")]:
        merged = merged.merge(df, on=["entity_lei", "reference_date"], how="outer")

    # Sum capital components (treat missing as 0 only when at least one is present)
    class_cols = ["cet1_amt", "at1_amt", "t2_amt"]
    any_present = merged[class_cols].notna().any(axis=1)
    merged["total_capital"] = merged[class_cols].sum(axis=1, min_count=1)

    # Compute ratio
    merged["total_capital_ratio"] = (
        merged["total_capital"] / merged["trea"].replace(0, pd.NA)
    )
    return merged[["entity_lei", "reference_date", "total_capital_ratio"]].loc[any_present]


def leverage_ratio(facts: pd.DataFrame) -> pd.DataFrame:
    """Leverage ratio (Tier 1 / TEM).

    Searches for a direct leverage ratio metric in K_91.00 first.
    If not found, computes Tier 1 / TEM as a proxy.
    """
    tpl = Template.TLAC1.value

    # Search for leverage ratio row
    mask = (
        (facts["template"] == tpl)
        & (facts["col_code"] == "0010")
        & facts["row_name"].fillna("").str.contains("leverage", case=False, regex=False)
    )
    candidates = facts.loc[mask, ["row_code", "row_name"]].drop_duplicates()

    if not candidates.empty:
        row_code = candidates.iloc[0]["row_code"]
        return _pick(facts, tpl, row_code, "0010").rename(
            columns={"value": "leverage_ratio"}
        )

    # Fallback: compute Tier1 / TEM
    tier1 = _pick(facts, tpl, "0020", "0010").rename(columns={"value": "tier1"})
    tem = _pick(facts, Template.KM2.value, "0060", "0010").rename(columns={"value": "tem"})

    if tier1.empty or tem.empty:
        return pd.DataFrame(columns=["entity_lei", "reference_date", "leverage_ratio"])

    merged = tier1.merge(tem, on=["entity_lei", "reference_date"], how="inner")
    merged["leverage_ratio"] = merged["tier1"] / merged["tem"].replace(0, pd.NA)
    return merged[["entity_lei", "reference_date", "leverage_ratio"]]


# ---- TLAC1 composition ----

# Five instrument classes used on the composition page.
# Each class maps to a list of TLAC1 rows summed at col c0010 (MREL amount).
TLAC1_COMPOSITION_CLASSES: dict[str, tuple[str, ...]] = {
    "cet1": ("0010",),
    "at1": ("0020",),
    "tier2": ("0060",),
    # Own issuance + intra-group + pre-2019 grandfathered + T2-residual.
    "subord_eligible_liabilities": ("0100", "0110", "0120", "0130"),
    # Pre-cap + pre-2019 grandfathered + post-Art 72b(3) capped non-subord.
    "senior_eligible_liabilities": ("0140", "0150", "0160"),
}


def tlac1_composition(facts: pd.DataFrame) -> pd.DataFrame:
    """Wide TLAC1 composition — one row per (bank, ref-date), five class columns.

    All amounts are euro values sourced from template K_91.00 column c0010
    (the MREL column). A ``total_stack`` column sums the five classes so
    callers can render either a 100% stacked view or an absolute-euro view.
    """
    tpl = Template.TLAC1.value
    out: pd.DataFrame | None = None
    for cls, rows in TLAC1_COMPOSITION_CLASSES.items():
        accum: pd.DataFrame | None = None
        for row in rows:
            slice_ = _pick(facts, tpl, row, "0010").rename(columns={"value": cls})
            if accum is None:
                accum = slice_
            else:
                accum = accum.merge(
                    slice_, on=["entity_lei", "reference_date"],
                    how="outer", suffixes=("", "__r"),
                )
                accum[cls] = accum[cls].fillna(0) + accum[f"{cls}__r"].fillna(0)
                accum = accum.drop(columns=[f"{cls}__r"])
        assert accum is not None
        out = accum if out is None else out.merge(
            accum, on=["entity_lei", "reference_date"], how="outer"
        )

    assert out is not None
    # Total stack = sum of the five classes (treating missing as 0 only when
    # at least one class is present, to avoid manufacturing a zero row).
    class_cols = list(TLAC1_COMPOSITION_CLASSES)
    any_present = out[class_cols].notna().any(axis=1)
    out["total_stack"] = out[class_cols].sum(axis=1, min_count=1)
    out = out.loc[any_present].copy()
    return out.sort_values(["entity_lei", "reference_date"]).reset_index(drop=True)


# ---- TLAC3 maturity profile ----

# Maturity-bucket rows in K_97.00.
TLAC3_MATURITY_BUCKETS: dict[str, tuple[str, str]] = {
    "maturity_1_to_2y":   ("0060", "1–2y"),
    "maturity_2_to_5y":   ("0070", "2–5y"),
    "maturity_5_to_10y":  ("0080", "5–10y"),
    "maturity_10y_plus":  ("0090", "10y+"),
    "maturity_perpetual": ("0100", "Perpetual"),
}

# Total MREL-eligible (denominator) — row 0050 col 0050 ("Sum of 1 to n").
TLAC3_TOTAL_ROW = "0050"
TLAC3_SUM_COL = "0050"


def tlac3_maturity(facts: pd.DataFrame) -> pd.DataFrame:
    """Wide maturity profile — shares of MREL-eligible liabilities by bucket.

    Uses K_97.00 col c0050 ('Sum of 1 to n'), which aggregates the amount
    across every insolvency rank for a given bucket. Bucket shares sum to
    1.0 (within rounding) because MREL-eligible liabilities must have
    residual maturity ≥ 1 year; there is no <1y bucket.
    """
    tpl = Template.TLAC3.value
    total = _pick(facts, tpl, TLAC3_TOTAL_ROW, TLAC3_SUM_COL).rename(
        columns={"value": "total_eligible"}
    )
    if total.empty:
        return pd.DataFrame(
            columns=["entity_lei", "reference_date", "total_eligible",
                     *TLAC3_MATURITY_BUCKETS]
        )

    out = total
    for bucket, (row, _label) in TLAC3_MATURITY_BUCKETS.items():
        slice_ = _pick(facts, tpl, row, TLAC3_SUM_COL).rename(columns={"value": bucket})
        out = out.merge(slice_, on=["entity_lei", "reference_date"], how="left")

    # Shares
    for bucket in TLAC3_MATURITY_BUCKETS:
        share_col = f"{bucket}_share"
        out[share_col] = out[bucket].fillna(0) / out["total_eligible"].replace(0, pd.NA)

    # Short-maturity index (< 2y share) — default sort on the page.
    out["under_2y_share"] = out["maturity_1_to_2y_share"]
    return out.sort_values(["entity_lei", "reference_date"]).reset_index(drop=True)


# ---- Creditor ranking (TLAC3 / TLAC3b) ----

# Per-scope mapping: (template, eligible-row, col). Column 0010 holds the
# per-rank amount; the open_key field tags the insolvency rank.
CREDITOR_RANK_SOURCES: dict[str, tuple[str, str, str]] = {
    "resolution":     (Template.TLAC3.value,  "0050", "0010"),
    "non_resolution": (Template.TLAC3B.value, "0020", "0010"),
}

_RANK_PATTERN = re.compile(r"Rank\s+(\d+)", re.IGNORECASE)


def creditor_rank_breakdown(
    facts: pd.DataFrame, *, scope: str = "resolution"
) -> pd.DataFrame:
    """Long-format MREL-eligible amount per (bank, ref-date, insolvency rank).

    ``scope='resolution'`` uses TLAC3 (K_97.00 row 0050); ``'non_resolution'``
    uses TLAC3b (K_98.00 row 0020). Rows with zero amount are kept so the
    caller can decide whether to drop them before stacking.
    """
    if scope not in CREDITOR_RANK_SOURCES:
        raise ValueError(f"Unknown creditor-rank scope: {scope!r}")
    tpl, row, col = CREDITOR_RANK_SOURCES[scope]

    if facts.empty:
        return pd.DataFrame(columns=["entity_lei", "reference_date",
                                     "rank", "value"])

    mask = (
        (facts["template"] == tpl)
        & (facts["row_code"] == row)
        & (facts["col_code"] == col)
        & facts["open_key"].fillna("").str.contains("Rank", case=False, na=False)
    )
    sub = facts.loc[mask, ["entity_lei", "reference_date", "open_key", "value"]].copy()
    if sub.empty:
        return pd.DataFrame(columns=["entity_lei", "reference_date",
                                     "rank", "value"])

    sub["rank"] = (
        sub["open_key"].str.extract(_RANK_PATTERN, expand=False).astype("Int64")
    )
    sub = sub.dropna(subset=["rank"])
    sub["rank"] = sub["rank"].astype(int)
    out = sub[["entity_lei", "reference_date", "rank", "value"]]
    return out.sort_values(["entity_lei", "reference_date", "rank"]).reset_index(drop=True)
