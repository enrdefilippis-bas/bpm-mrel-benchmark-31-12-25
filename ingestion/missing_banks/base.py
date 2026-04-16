"""Base class for per-bank Pillar 3 parsers.

The EBA cell-level export covers 112 banks, but Banco BPM's natural peer
set includes several banks that file Pillar 3 separately and are not in
the export (Intesa, UniCredit S.p.A., BBVA, Crédit Agricole S.A.,
Société Générale). Each such bank gets its own subclass of
:class:`BaseBankParser` and contributes facts to the canonical table.

Two ingestion paths are supported:

1. **Manual entries** — a JSON file with KM2 / TLAC1 headline cells hand
   read from the bank's published Pillar 3 disclosure. Fast to bootstrap
   the peer set when automated PDF parsing is not yet in place.
2. **PDF parsing** — subclasses may override :meth:`parse_pdf` to
   extract the same cells automatically from an IR-published PDF. The
   default implementation raises :class:`NotImplementedError` so callers
   can catch it and fall back to manual entries.
"""
from __future__ import annotations

import json
from abc import ABC
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

import pandas as pd

from core.schema import (
    FACT_COLUMNS,
    Template,
    UnitType,
    empty_facts,
    validate_facts,
)


# KM2 (K_90.01) headline cells — metric-key → (row_code, col_code, unit).
# These are the cells the UI derives ratios, totals and cushions from.
KM2_CELLS: dict[str, tuple[str, str, UnitType]] = {
    "mrel_total_amount":            ("0010", "0010", UnitType.AMOUNT_EUR),
    "trea":                         ("0030", "0010", UnitType.AMOUNT_EUR),
    "mrel_pct_trea":                ("0040", "0010", UnitType.RATIO),
    "subord_pct_trea":              ("0050", "0010", UnitType.RATIO),
    "tem":                          ("0060", "0010", UnitType.AMOUNT_EUR),
    "mrel_pct_tem":                 ("0070", "0010", UnitType.RATIO),
    "subord_pct_tem":               ("0080", "0010", UnitType.RATIO),
    "mrel_requirement_trea":        ("0120", "0010", UnitType.RATIO),
    "mrel_subord_requirement_trea": ("0130", "0010", UnitType.RATIO),
    "mrel_requirement_tem":         ("0140", "0010", UnitType.RATIO),
    "mrel_subord_requirement_tem":  ("0150", "0010", UnitType.RATIO),
}

# TLAC1 (K_91.00) composition cells — class-key → row_code (col always c0010).
# Matches the five-class grouping used on the composition page.
TLAC1_CELLS: dict[str, str] = {
    "cet1":                  "0010",
    "at1":                   "0020",
    "tier2":                 "0060",
    "subord_own_issuance":   "0100",
    "subord_intra_group":    "0110",
    "subord_grandfathered":  "0120",
    "subord_t2_residual":    "0130",
    "senior_pre_cap":        "0140",
    "senior_grandfathered":  "0150",
    "senior_post_cap":       "0160",
}


@dataclass(frozen=True)
class BankMeta:
    """Static metadata about a bank handled by a :class:`BaseBankParser`."""

    lei: str
    name: str
    country: str
    source_tag: str                 # Source enum value ("pdf-intesa" etc.)
    pillar3_url_pattern: str        # URL template with {year} / {quarter}
    ir_page: str                    # fallback landing page if the PDF URL drifts


class BaseBankParser(ABC):
    """ABC for bank-specific Pillar 3 parsers.

    Subclasses declare metadata on the ``meta`` class variable. The
    default ``from_manual_entries`` implementation is sufficient for
    all current missing banks — subclasses only need to override
    :meth:`parse_pdf` when automated extraction is added.
    """

    meta: ClassVar[BankMeta]

    # ---- Manual-entry path ---------------------------------------------------

    @classmethod
    def from_manual_entries(cls, entries_path: Path | str) -> pd.DataFrame:
        """Build a canonical facts frame from a JSON entries file.

        The JSON has one block per reference date under ``reference_dates``,
        with sub-blocks ``km2`` and optionally ``tlac1``. Cells whose
        value is ``null`` are skipped — the analyst only fills what they
        have from the Pillar 3 PDF. Ratios are expected as decimals
        (0.3402 for 34.02%), consistent with the EBA export convention.
        """
        entries_path = Path(entries_path)
        if not entries_path.exists():
            return empty_facts()

        payload = json.loads(entries_path.read_text())
        entity_name = payload.get("entity_name", cls.meta.name)
        per_date = payload.get("reference_dates", {})
        if not per_date:
            return empty_facts()

        now = pd.Timestamp.now("UTC").tz_localize(None)
        rows: list[dict] = []

        for date_iso, day in per_date.items():
            ref_date = pd.Timestamp(date_iso)

            km2 = day.get("km2") or {}
            for metric, (row_code, col_code, unit) in KM2_CELLS.items():
                value = km2.get(metric)
                if value is None:
                    continue
                rows.append(cls._fact_row(
                    entity_name=entity_name, ref_date=ref_date,
                    template=Template.KM2.value,
                    row_code=row_code, col_code=col_code,
                    value=float(value), unit=unit, now=now,
                ))

            tlac1 = day.get("tlac1") or {}
            for cls_key, row_code in TLAC1_CELLS.items():
                value = tlac1.get(cls_key)
                if value is None:
                    continue
                rows.append(cls._fact_row(
                    entity_name=entity_name, ref_date=ref_date,
                    template=Template.TLAC1.value,
                    row_code=row_code, col_code="0010",
                    value=float(value), unit=UnitType.AMOUNT_EUR, now=now,
                ))

        if not rows:
            return empty_facts()

        df = pd.DataFrame(rows)
        df = df.astype({k: v for k, v in FACT_COLUMNS.items() if k in df})
        return validate_facts(df)

    # ---- PDF path (subclass hook) --------------------------------------------

    @classmethod
    def parse_pdf(cls, pdf_path: Path | str) -> pd.DataFrame:
        """Extract KM2 + TLAC1 cells from a Pillar 3 PDF.

        Default implementation raises NotImplementedError. Subclasses
        should populate this once a stable extraction pattern exists
        for that bank's template (tables vary across issuers).
        """
        raise NotImplementedError(
            f"PDF parsing not yet implemented for {cls.meta.name}. "
            f"Populate the manual-entries JSON instead."
        )

    # ---- Internals -----------------------------------------------------------

    @classmethod
    def _fact_row(
        cls, *, entity_name: str, ref_date: pd.Timestamp, template: str,
        row_code: str, col_code: str, value: float, unit: UnitType,
        now: pd.Timestamp,
    ) -> dict:
        return {
            "entity_lei":     cls.meta.lei,
            "entity_name":    entity_name,
            "country":        cls.meta.country,
            "reference_date": ref_date,
            "template":       template,
            "row_code":       row_code,
            "row_name":       "",
            "col_code":       col_code,
            "col_name":       "",
            "open_key":       "",
            "raw_value":      value,
            "value":          value,
            "unit":           unit.value,
            "source":         cls.meta.source_tag,
            "ingested_at":    now,
        }
