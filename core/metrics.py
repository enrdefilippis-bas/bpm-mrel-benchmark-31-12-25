"""Derive analyst-facing metrics from the canonical facts table.

Each function takes the full facts DataFrame and returns a wide
per-(bank, ref-date) table keyed by `entity_lei` + `reference_date`.
Callers combine columns for the various pages.
"""
from __future__ import annotations

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
