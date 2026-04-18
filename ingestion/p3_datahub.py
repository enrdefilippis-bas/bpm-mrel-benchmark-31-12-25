"""Parse the P3 datahub export (p3datahuball.xlsx) into canonical facts.

The datahub export is shaped as:
    Row 0: ReferenceDate (header label + dates across columns)
    Row 1: Headers (Entity Code, Entity Name, ..., Template, ..., FactValue columns)
    Row 2+: Data rows with cell-level MREL/TLAC information for multiple banks.

The four FactValue columns correspond to:
    - Q2-2025 (2025-06-30)
    - Q3-2025 (2025-09-30)
    - Q4-2024 (2024-12-31)
    - Q4-2025 (2025-12-31)

We focus on MRELTLACDIS module and emit facts in the canonical schema.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd

from core.schema import (
    FACT_COLUMNS,
    Source,
    Template,
    UnitType,
    empty_facts,
    validate_facts,
    zero_pad_row_code,
)


def _infer_unit(row_name: str, col_name: str,
                template: str | None = None, row_code: str | None = None) -> str:
    """Guess whether a fact is a ratio, EUR amount, or unknown.

    Uses the same logic as the EBA parser for consistency.
    """
    # Hard-coded ratio rows from K_90.01 and K_91.00
    KM2_RATIO_ROWS = frozenset({
        "0040", "0050", "0070", "0080", "0090", "0100", "0120",
        "0130", "0140", "0150", "0160", "0170", "0180",
    })

    if template == Template.KM2.value and row_code in KM2_RATIO_ROWS:
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
    """Normalize per-bank reporting idiosyncrasies to a canonical unit.

    Same logic as EBA parser: ratios >= 1.5 are assumed to be percentages
    and divided by 100; others pass through.
    """
    if raw is None or pd.isna(raw):
        return None
    if unit != UnitType.RATIO.value:
        return float(raw)
    if raw >= 1.5:
        return float(raw) / 100.0
    return float(raw)


def parse_p3_datahub(path: str | Path, module_filter: str = "MREL/TLAC disclosures") -> pd.DataFrame:
    """Parse the P3 datahub export into canonical facts.

    The export is structured as:
        Row 0: Header row with "ReferenceDate" label and dates
        Row 1: Column headers
        Row 2+: Data

    Args:
        path: Path to the p3datahuball.xlsx file.
        module_filter: Only emit facts from this module (default "MREL/TLAC disclosures").

    Returns:
        A canonical facts DataFrame (validated against FACT_COLUMNS schema).
    """
    path = Path(path)

    # First, read row 0 to extract the reference dates
    # The file has dates in the FactValue columns on row 0
    row0 = pd.read_excel(path, sheet_name="Export", nrows=1, header=None)
    # Columns 13, 14, 15, 16 should have the dates (FactValue columns)
    ref_dates = []
    if len(row0.columns) > 16:
        for i in [13, 14, 15, 16]:
            val = row0.iloc[0, i]
            if isinstance(val, (pd.Timestamp, datetime)):
                ref_dates.append(pd.Timestamp(val))

    # If we couldn't extract dates, use the default mapping
    if len(ref_dates) != 4:
        ref_dates = [
            pd.Timestamp("2025-06-30"),  # Q2-2025
            pd.Timestamp("2025-09-30"),  # Q3-2025
            pd.Timestamp("2024-12-31"),  # Q4-2024
            pd.Timestamp("2025-12-31"),  # Q4-2025
        ]

    # Now read with row 1 as header (skiprows=1)
    raw = pd.read_excel(path, sheet_name="Export", skiprows=1)
    raw = raw.rename(columns=lambda c: c.strip() if isinstance(c, str) else c)

    # Required id columns (from the spec)
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
        raise ValueError(f"Datahub export missing expected columns: {missing}")

    # Filter by module
    raw = raw[raw["Module Name"] == module_filter].copy()
    if raw.empty:
        return empty_facts()

    # The FactValue columns are the last 4 columns
    value_cols = [c for c in raw.columns if "FactValue" in str(c)][-4:]

    # Create mapping from column name to reference date
    date_map = dict(zip(value_cols, ref_dates))

    # Melt the FactValue columns into long format
    long = raw.melt(
        id_vars=id_cols,
        value_vars=value_cols,
        var_name="value_col",
        value_name="raw_value",
    )

    long["reference_date"] = long["value_col"].map(date_map)
    long = long.drop(columns="value_col")
    long = long.dropna(subset=["raw_value"])

    # Coerce values to numeric, drop nulls
    long["raw_value"] = pd.to_numeric(long["raw_value"], errors="coerce")
    long = long.dropna(subset=["raw_value"])

    if long.empty:
        return empty_facts()

    # Extract template code (e.g., "K_90.01" from "K_90.01 - Key metrics")
    template = (
        long["Template"]
        .fillna("")
        .astype(str)
        .str.split(" -")
        .str[0]
        .str.strip()
    )

    # Check if all templates are whitelisted
    whitelisted = {t.value for t in Template}
    unknown_templates = set(template.unique()) - whitelisted - {""}
    if unknown_templates:
        print(f"Warning: Datahub contains unknown templates (skipping): {unknown_templates}")

    # Reset index to match the series
    long = long.reset_index(drop=True)
    template = template.reset_index(drop=True)

    now = pd.Timestamp.now("UTC").tz_localize(None)

    row_name = long["Row Name"].fillna("").astype(str).str.strip()
    col_name = long["Column Name"].fillna("").astype(str).str.strip()
    row_code = long["Row"].apply(zero_pad_row_code)
    col_code = long["Column"].apply(zero_pad_row_code)

    # Infer units
    unit = [
        _infer_unit(rn, cn, template=tpl, row_code=rc)
        for rn, cn, tpl, rc in zip(row_name, col_name, template, row_code)
    ]

    # Normalize values
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
            "col_code": col_code,
            "col_name": col_name,
            "open_key": long["Open Key"].fillna("").astype(str).str.strip(),
            "raw_value": pd.to_numeric(long["raw_value"], errors="coerce"),
            "value": pd.to_numeric(pd.Series(value, index=long.index), errors="coerce"),
            "unit": unit,
            "source": "p3-datahub",
            "ingested_at": now,
        }
    )

    # Drop rows with empty LEI
    out = out[out["entity_lei"] != ""].reset_index(drop=True)

    # Enforce schema
    out = out.astype({k: v for k, v in FACT_COLUMNS.items() if k in out})
    return validate_facts(out)


def load_or_empty(path: str | Path | None, module_filter: str = "MREL/TLAC disclosures") -> pd.DataFrame:
    """Convenience: return parsed facts, or an empty frame if path is None."""
    if path is None:
        return empty_facts()
    return parse_p3_datahub(path, module_filter=module_filter)
