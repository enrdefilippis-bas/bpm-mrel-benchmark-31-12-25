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
