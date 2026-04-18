"""Crédit Agricole S.A. Pillar 3 parser."""
from __future__ import annotations

from pathlib import Path
import re

import pandas as pd
import pdfplumber

from core.schema import Source

from .base import BankMeta, BaseBankParser
from ._pdf_utils import parse_number


class CreditAgricoleParser(BaseBankParser):
    """Crédit Agricole S.A. Pillar 3 parser.

    STRATEGY:
    - Page 87 has KM2 ratios (EU-7 through EU-10) but no amounts.
    - Page 88 has the EU-TLAC1 table containing all the amounts we need:
        mrel_total_amount (row 22), TREA (row 23), TEM (row 24),
        CET1 (row 1), AT1 (row 2), Tier 2 (row 6), and composition.

    Number format: ANGLO (210,698 = 210.698 million EUR, comma is thousands
    separator). Ratios like "31.79%" (dot decimal).

    Tuned for 2025Q4 PDF layout; may need updating for future quarters.
    """

    meta = BankMeta(
        lei="R0MUWSFPU8MPRO8K5P83",
        name="Crédit Agricole S.A.",
        country="France",
        source_tag=Source.PDF_CREDIT_AGRICOLE.value,
        pillar3_url_pattern=(
            "https://www.credit-agricole.com/var/ca/storage/original/"
            "{year}{month:02d}/pillar-3-risk-report-{year}-q{quarter_num}.pdf"
        ),
        ir_page=(
            "https://www.credit-agricole.com/en/investors/financial-information/"
            "risk-reports"
        ),
    )

    # Window of pages to read (0-indexed). KM2 ratios live on ~page 87, the
    # TLAC1 amounts on ~page 88. Reading a narrow window avoids a multi-minute
    # full-text extraction on a 405-page PDF.
    _PAGE_WINDOW: tuple[int, int] = (80, 95)

    @classmethod
    def parse_pdf(cls, pdf_path: Path | str) -> pd.DataFrame:
        pdf_path = Path(pdf_path)

        per_date = {"2025-12-31": {"km2": {}, "tlac1": {}}}
        km2 = per_date["2025-12-31"]["km2"]
        tlac1 = per_date["2025-12-31"]["tlac1"]

        with pdfplumber.open(pdf_path) as pdf:
            start = max(0, cls._PAGE_WINDOW[0])
            end = min(len(pdf.pages), cls._PAGE_WINDOW[1])
            full_text = "\n".join(
                (pdf.pages[i].extract_text() or "") for i in range(start, end)
            )

        def _amt(pattern: str) -> float | None:
            m = re.search(pattern, full_text, re.MULTILINE | re.DOTALL)
            if not m:
                return None
            v = parse_number(m.group(1), european=False)
            return v * 1_000_000 if v is not None else None

        def _pct(pattern: str) -> float | None:
            m = re.search(pattern, full_text, re.MULTILINE | re.DOTALL)
            if not m:
                return None
            v = parse_number(m.group(1), european=False)
            return v / 100.0 if v is not None else None

        # === STRICT TIER: amounts (from TLAC1 table, page 88) ===
        # Row 22 "Own funds and eligible liabilities after adjustments 210,698 ..."
        km2["mrel_total_amount"] = _amt(
            r"^22\s+Own funds and eligible liabilities after adjustments\s+([\d,]+)"
        )
        # Row 23 "Total risk exposure amount (TREA) (2) 662,703 ..."
        km2["trea"] = _amt(
            r"^23\s+Total risk exposure amount \(TREA\).*?\s([\d,]{4,})\s"
        )
        # Row 24 "Total exposure measure (TEM) (2) 2,214,046 ..."
        km2["tem"] = _amt(
            r"^24\s+Total exposure measure \(TEM\).*?\s([\d,]{6,})\s"
        )
        # Row 1 "Common Equity Tier 1 capital (CET1) 114,581 ..."
        tlac1["cet1"] = _amt(
            r"^1\s+Common Equity Tier 1 capital \(CET1\)\s+([\d,]+)"
        )
        # Row 2 "Additional Tier 1 capital (AT1) 7,998 ..."
        tlac1["at1"] = _amt(
            r"^2\s+Additional Tier 1 capital \(AT1\)\s+([\d,]+)"
        )
        # Row 6 "Tier 2 capital (T2) 16,147 ..."
        tlac1["tier2"] = _amt(
            r"^6\s+Tier 2 capital \(T2\)\s+([\d,]+)"
        )

        # Validate strict tier up-front with clear errors.
        missing_strict = [k for k in
            ("mrel_total_amount", "trea", "tem") if km2.get(k) is None]
        missing_tlac = [k for k in ("cet1", "at1", "tier2") if tlac1.get(k) is None]
        if missing_strict or missing_tlac:
            raise ValueError(
                "Crédit Agricole parser: could not locate required cells "
                f"KM2={missing_strict} TLAC1={missing_tlac}. "
                "PDF layout may have changed; inspect pages 85-90."
            )

        # === SOFT TIER: KM2 ratios (page 87) ===
        km2["mrel_pct_trea"] = _pct(
            r"OWN FUNDS AND ELIGIBLE LIABILITIES AS A PERCENTAGE OF TREA\s+([\d.]+)%"
        )
        km2["subord_pct_trea"] = _pct(
            r"EU-25a of which own funds and subordinated liabilities\s+([\d.]+)%"
        )
        km2["mrel_pct_tem"] = _pct(
            r"OWN FUNDS AND ELIGIBLE LIABILITIES AS A PERCENTAGE OF TEM\s+([\d.]+)%"
        )
        km2["subord_pct_tem"] = _pct(
            r"EU-26a of which own funds and subordinated liabilities\s+([\d.]+)%"
        )
        km2["mrel_requirement_trea"] = _pct(
            r"EU-7 MREL EXPRESSED AS A PERCENTAGE OF THE TREA.*?\(4\)\s+([\d.]+)%"
        )
        km2["mrel_subord_requirement_trea"] = _pct(
            r"EU-8 of which to be met with own funds\s*or subordinated liabilities \(4\)\s+([\d.]+)%"
        )
        km2["mrel_requirement_tem"] = _pct(
            r"EU-9 MREL EXPRESSED AS A PERCENTAGE OF THE TEM\s+([\d.]+)%"
        )
        km2["mrel_subord_requirement_tem"] = _pct(
            r"EU-10 of which to be met with own funds\s*or subordinated liabilities\s+([\d.]+)%"
        )

        # === SOFT TIER: TLAC1 composition (page 88) ===
        tlac1["subord_own_issuance"] = _amt(
            r"^12\s+Eligible liabilities instruments issued directly by the resolution entity.*?subordinated to excluded liabilities \(not grandfathered\)\s+([\d,]+)"
        )
        tlac1["subord_t2_residual"] = _amt(
            r"^EU-12c Tier 2 instruments with a residual maturity of at least one year.*?do not qualify as Tier 2 items\s+([\d,]+)"
        )
        tlac1["senior_pre_cap"] = _amt(
            r"^13\s+Eligible liabilities that are not subordinated to excluded liabilities \(not grandfathered pre-cap\)\s+([\d,]+)"
        )
        tlac1["senior_grandfathered"] = _amt(
            r"^EU-13a Eligible liabilities that are not subordinated to excluded liabilities issued\s*prior to 27 June 2019 \(pre-cap\)\s+([\d,]+)"
        )

        # Drop None entries so _build_facts skips them cleanly.
        per_date["2025-12-31"]["km2"] = {k: v for k, v in km2.items() if v is not None}
        per_date["2025-12-31"]["tlac1"] = {k: v for k, v in tlac1.items() if v is not None}

        return cls._build_facts(per_date, entity_name=cls.meta.name)
