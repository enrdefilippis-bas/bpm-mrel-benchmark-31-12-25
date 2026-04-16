"""Canonical fact schema for the MREL peer-benchmark tool.

All ingested data — the EBA Pillar 3 export and each parsed bank PDF —
lands in one long-format facts DataFrame with the columns defined here.
Every downstream metric, chart and ranking derives from this table.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Final

import pandas as pd


class Template(str, Enum):
    """EBA Pillar 3 MREL/TLAC templates present in the export."""

    KM2 = "K_90.01"           # Key metrics - MREL / TLAC requirement
    TLAC1 = "K_91.00"         # Composition - MREL / TLAC
    ILAC = "K_93.00"          # Internal loss absorbing capacity (non-EU G-SIIs)
    CR_NON_RES = "K_95.00"    # Creditor ranking - entity that is not a resolution entity
    CR_NON_RES_B = "K_96.00"  # Creditor ranking - TLAC2b (non-resolution entity)
    TLAC3 = "K_97.00"         # Creditor ranking - resolution entity
    TLAC3B = "K_98.00"        # Creditor ranking - TLAC3b (resolution entity)
    NARRATIVE = "K_00.05"     # Accompanying narrative


class UnitType(str, Enum):
    """How a fact's numeric value should be interpreted."""

    AMOUNT_EUR = "amount_eur"    # absolute euros
    RATIO = "ratio"              # 0.1 = 10%, after normalization
    COUNT = "count"              # integer-ish (e.g. maturity-bucket amounts already in EUR → still AMOUNT_EUR)
    UNKNOWN = "unknown"


class Source(str, Enum):
    """Where a fact was ingested from."""

    EBA_EXPORT = "eba-export"
    PDF_INTESA = "pdf-intesa"
    PDF_UNICREDIT = "pdf-unicredit"
    PDF_BBVA = "pdf-bbva"
    PDF_CREDIT_AGRICOLE = "pdf-credit-agricole"
    PDF_SOCGEN = "pdf-socgen"


# Column names — one source of truth. Use these everywhere.
FACT_COLUMNS: Final[dict[str, str]] = {
    "entity_lei": "string",
    "entity_name": "string",
    "country": "string",
    "reference_date": "datetime64[ns]",
    "template": "string",
    "row_code": "string",         # zero-padded "0010", "0020", ...
    "row_name": "string",
    "col_code": "string",
    "col_name": "string",
    "open_key": "string",         # free-text key for rank/bucket breakdowns
    "raw_value": "Float64",       # as reported (may be decimal or percent for ratios)
    "value": "Float64",           # normalized (ratios always decimal; amounts in EUR)
    "unit": "string",             # UnitType value
    "source": "string",           # Source value
    "ingested_at": "datetime64[ns]",
}


@dataclass(frozen=True)
class Fact:
    """Single fact row. Mirrors FACT_COLUMNS."""

    entity_lei: str
    entity_name: str
    country: str
    reference_date: date
    template: str
    row_code: str
    row_name: str
    col_code: str
    col_name: str
    open_key: str
    raw_value: float | None
    value: float | None
    unit: str
    source: str
    ingested_at: datetime


def empty_facts() -> pd.DataFrame:
    """Return an empty facts DataFrame with the canonical dtypes."""
    return pd.DataFrame({name: pd.Series(dtype=dt) for name, dt in FACT_COLUMNS.items()})


def validate_facts(df: pd.DataFrame) -> pd.DataFrame:
    """Check a facts DataFrame matches the canonical schema.

    Returns the DataFrame unchanged on success; raises ValueError otherwise.
    """
    missing = set(FACT_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"Facts DataFrame is missing columns: {sorted(missing)}")
    extra = set(df.columns) - set(FACT_COLUMNS)
    if extra:
        raise ValueError(f"Facts DataFrame has unexpected columns: {sorted(extra)}")
    return df[list(FACT_COLUMNS)]


def zero_pad_row_code(value: object) -> str:
    """Normalize row codes to zero-padded 4-digit strings.

    The EBA export stores row codes as floats like 10.0, 20.0. XBRL cell
    references use "0010", "0020". We align to the XBRL convention.
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return ""
        try:
            n = int(float(s))
        except ValueError:
            return s
    else:
        try:
            n = int(float(value))  # handles np.float64 too
        except (TypeError, ValueError):
            return str(value)
    return f"{n:04d}"
