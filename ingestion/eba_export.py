"""Parse the EBA Pillar 3 MREL/TLAC cell-level export into canonical facts.

The export is shaped as:

    row 0: ReferenceDate ... <date_q2> <date_q3> <date_q4>
    row 1: Entity Code | Entity Name | ... | FactValue | FactValue | FactValue
    row 2+: one row per (bank, template, row_code, column, open_key)

The three trailing FactValue columns hold the numeric values for the
three reference dates at row 0. We pivot them out into long format
(one row per bank × cell × ref_date).
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd

from core.schema import (
    FACT_COLUMNS,
    Source,
    UnitType,
    empty_facts,
    validate_facts,
    zero_pad_row_code,
)


def _read_reference_dates(path: Path) -> list[pd.Timestamp]:
    """Row 0 of the sheet holds up to three quarter-end dates."""
    row0 = pd.read_excel(path, header=None, nrows=1).iloc[0]
    dates = [v for v in row0 if isinstance(v, (pd.Timestamp, datetime))]
    if not dates:
        raise ValueError(f"No reference dates found on row 0 of {path}")
    return [pd.Timestamp(d) for d in dates]


# KM2 (K_90.01) rows that are always ratios — "of which" sub-rows inherit
# the unit of the parent ratio row even though their text doesn't mention
# "percentage". Hard-coding these prevents misclassification of cells like
# row 0050 ("of which own funds and subordinated liabilities") which reads
# like an amount row but is actually a ratio.
KM2_RATIO_ROWS: frozenset[str] = frozenset({
    "0040",  # 3. Own funds and eligible liabilities as % of TREA
    "0050",  # EU-3a. Of which own funds and subordinated liabilities
    "0070",  # 5. Own funds and eligible liabilities as % of TEM
    "0080",  # EU-5a. Of which own funds and subordinated liabilities
    "0090",  # 6. Does the resolution entity subordinate …? (flag, but ratio-like)
    "0100",  # 7. ...
    "0120",  # 9. MREL requirement as % of TREA
    "0130",  # 10. Of which to be met with subordinated instruments (% TREA)
    "0140",  # 11. MREL requirement as % of TEM
    "0150",  # 12. Of which to be met with subordinated instruments (% TEM)
    "0160",  # 13. Combined buffer requirement
    "0170",  # 14. Of which …
    "0180",  # 15. ...
})


def _infer_unit(row_name: str, col_name: str, *,
                template: str | None = None, row_code: str | None = None) -> str:
    """Guess whether a fact is a ratio, EUR amount, or unknown.

    Strategy:
    1. For well-known ratio rows (e.g. KM2 'of which …' sub-rows), use the
       template+row_code mapping so ambiguous row names don't misclassify.
    2. Otherwise fall back to string heuristics on row/col name.
    """
    if template == "K_90.01" and row_code in KM2_RATIO_ROWS:
        return UnitType.RATIO.value

    text = f"{row_name or ''} {col_name or ''}".lower()
    if any(token in text for token in ("percentage", "% of", "ratio", " %")):
        return UnitType.RATIO.value
    if any(
        token in text
        for token in (
            "amount",
            "own funds",
            "liabilities",
            "capital",
            "exposure measure",
            "risk exposure",
            "common equity",
            "additional tier",
            "tier 2",
            "items",
        )
    ):
        return UnitType.AMOUNT_EUR.value
    return UnitType.UNKNOWN.value


def _normalize_value(raw: float | None, unit: str) -> float | None:
    """Convert per-bank reporting idiosyncrasies to a canonical unit.

    Some banks (notably Norwegian SpareBanks, Belfius, Addiko) report
    ratio cells as raw percent (e.g., 32.33 meaning 32.33%). Most banks
    report as a decimal (0.3233). We fold both to decimal: values >= 1.5
    are interpreted as already-in-percent and divided by 100. EUR amounts
    pass through.
    """
    if raw is None or pd.isna(raw):
        return None
    if unit != UnitType.RATIO.value:
        return float(raw)
    if raw >= 1.5:
        return float(raw) / 100.0
    return float(raw)


def parse_eba_export(path: str | Path) -> pd.DataFrame:
    """Return a canonical facts DataFrame for the full Excel export."""
    path = Path(path)
    ref_dates = _read_reference_dates(path)

    raw = pd.read_excel(path, header=1)
    raw = raw.rename(columns=lambda c: c.strip() if isinstance(c, str) else c)

    value_cols = [c for c in raw.columns if c == "FactValue" or c.startswith("FactValue.")]
    if len(value_cols) != len(ref_dates):
        raise ValueError(
            f"Expected {len(ref_dates)} value columns to match ref-dates {ref_dates}, "
            f"got {value_cols}"
        )

    # Melt the three FactValue columns into a single row per ref_date.
    id_cols = [
        "Entity Code",
        "Entity Name",
        "Country",
        "Module Name",
        "ModuleCode",
        "Cell",
        "Open Key",
        "Template",
        "Row",
        "Row Name",
        "Column",
        "Column Name",
        "Sheet",
    ]
    missing = [c for c in id_cols if c not in raw.columns]
    if missing:
        raise ValueError(f"Export is missing expected id columns: {missing}")

    long = raw.melt(
        id_vars=id_cols,
        value_vars=value_cols,
        var_name="value_col",
        value_name="raw_value",
    )
    col_to_date = dict(zip(value_cols, ref_dates))
    long["reference_date"] = long["value_col"].map(col_to_date)
    long = long.drop(columns="value_col")
    long = long.dropna(subset=["raw_value"])

    # Narrative template K_00.05 holds free-text commentary, not numbers.
    # Drop it before numeric coercion so unrelated strings don't leak in.
    long = long[~long["Template"].astype(str).str.startswith("K_00.05", na=False)]
    long["raw_value"] = pd.to_numeric(long["raw_value"], errors="coerce")
    long = long.dropna(subset=["raw_value"])

    template = long["Template"].fillna("").astype(str).str.split(" -").str[0].str.strip()
    now = pd.Timestamp.now("UTC").tz_localize(None)

    row_name = long["Row Name"].fillna("").astype(str).str.strip()
    col_name = long["Column Name"].fillna("").astype(str).str.strip()

    row_code = long["Row"].apply(zero_pad_row_code)
    unit = [
        _infer_unit(rn, cn, template=tpl, row_code=rc)
        for rn, cn, tpl, rc in zip(row_name, col_name, template, row_code)
    ]
    value = [_normalize_value(rv, u) for rv, u in zip(long["raw_value"], unit)]

    out = pd.DataFrame(
        {
            "entity_lei": long["Entity Code"].fillna("").astype(str).str.strip(),
            "entity_name": long["Entity Name"].fillna("").astype(str).str.strip(),
            "country": long["Country"].fillna("").astype(str).str.strip(),
            "reference_date": long["reference_date"],
            "template": template,
            "row_code": row_code,
            "row_name": row_name,
            "col_code": long["Column"].apply(zero_pad_row_code),
            "col_name": col_name,
            "open_key": long["Open Key"].fillna("").astype(str).str.strip(),
            "raw_value": pd.to_numeric(long["raw_value"], errors="coerce"),
            "value": pd.to_numeric(pd.Series(value, index=long.index), errors="coerce"),
            "unit": unit,
            "source": Source.EBA_EXPORT.value,
            "ingested_at": now,
        }
    )

    out = out[out["entity_lei"] != ""].reset_index(drop=True)
    out = out.astype({k: v for k, v in FACT_COLUMNS.items() if k in out})
    return validate_facts(out)


def load_or_empty(path: str | Path | None) -> pd.DataFrame:
    """Convenience: return parsed facts, or an empty frame if path is None."""
    if path is None:
        return empty_facts()
    return parse_eba_export(path)
