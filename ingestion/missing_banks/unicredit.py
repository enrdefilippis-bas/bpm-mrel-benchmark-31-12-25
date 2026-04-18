"""UniCredit S.p.A. Pillar 3 parser."""
from __future__ import annotations

from pathlib import Path
import re

import pandas as pd
import pdfplumber

from core.schema import Source

from .base import BankMeta, BaseBankParser
from ._pdf_utils import parse_number


class UniCreditParser(BaseBankParser):
    """UniCredit S.p.A. Pillar 3 parser.

    STRATEGY: Page 33 contains KM2 and TLAC1 metrics in English.
    Number format: Anglo (1,234.56). Amounts in millions EUR;
    multiply by 1M to get EUR. Ratios as percentages (30.59% -> 0.3059).

    Tuned for 2025Q4 PDF layout; may need updating for future quarters.
    """

    meta = BankMeta(
        lei="549300TRUWO2CD2G5692",
        name="UniCredit S.p.A.",
        country="Italy",
        source_tag=Source.PDF_UNICREDIT.value,
        pillar3_url_pattern=(
            "https://www.unicreditgroup.eu/content/dam/unicreditgroup-eu/documents/en/"
            "investors/financial-reports/{year}/4Q{year_short}/"
            "UniCredit_Pillar_3_{year}_{quarter}.pdf"
        ),
        ir_page=(
            "https://www.unicreditgroup.eu/en/investors/financial-reports.html"
        ),
    )

    @classmethod
    def parse_pdf(cls, pdf_path: Path | str) -> pd.DataFrame:
        """Extract KM2 and TLAC1 from UniCredit PDF.

        KM2: Page 33 has key metrics in EU KM2 format.
        TLAC1: Derived from KM2 where available.
        Anglo format (1,234.56). Amounts in millions EUR.
        Ratios as percentages (30.59% -> 0.3059).
        """
        pdf_path = Path(pdf_path)

        per_date = {"2025-12-31": {"km2": {}, "tlac1": {}}}
        km2 = per_date["2025-12-31"]["km2"]
        tlac1 = per_date["2025-12-31"]["tlac1"]

        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Page 33 for KM2 and TLAC1 metrics (EU format)
                if len(pdf.pages) < 33:
                    raise ValueError("PDF has fewer than 33 pages")
                    
                page33_text = pdf.pages[32].extract_text() or ""

                # === KM2 AMOUNTS (STRICT TIER) ===
                # Pattern: "1 Own Funds and eligible liabilities 90,655"
                mrel_match = re.search(
                    r'^1\s+Own Funds and eligible liabilities\s+(\d+[.,]\d+)$',
                    page33_text, re.MULTILINE
                )
                if mrel_match:
                    km2["mrel_total_amount"] = parse_number(mrel_match.group(1), european=False) * 1_000_000
                else:
                    raise ValueError("Could not extract mrel_total_amount")

                # Pattern: "2 Total risk exposure amount of the resolution group (TREA) 296,327"
                trea_match = re.search(
                    r'^2\s+Total risk exposure amount of the resolution group \(TREA\)\s+(\d+[.,]\d+)$',
                    page33_text, re.MULTILINE
                )
                if trea_match:
                    km2["trea"] = parse_number(trea_match.group(1), european=False) * 1_000_000
                else:
                    raise ValueError("Could not extract trea")

                # Pattern: "4 Total exposure measure (TEM) of the resolution group 906,925"
                tem_match = re.search(
                    r'^4\s+Total exposure measure \(TEM\) of the resolution group\s+(\d+[.,]\d+)$',
                    page33_text, re.MULTILINE
                )
                if tem_match:
                    km2["tem"] = parse_number(tem_match.group(1), european=False) * 1_000_000
                else:
                    raise ValueError("Could not extract tem")

                # === TLAC1 COMPOSITION (STRICT TIER) ===
                # Pattern: "1 Common Equity Tier 1 capital (CET1) 43,700"
                cet1_match = re.search(
                    r'^1\s+Common Equity Tier 1 capital \(CET1\)\s+(\d+[.,]\d+)$',
                    page33_text, re.MULTILINE
                )
                if cet1_match:
                    tlac1["cet1"] = parse_number(cet1_match.group(1), european=False) * 1_000_000
                else:
                    raise ValueError("Could not extract cet1")

                # Pattern: "2 Additional Tier 1 capital (AT1) 4,956"
                at1_match = re.search(
                    r'^2\s+Additional Tier 1 capital \(AT1\)\s+(\d+[.,]\d+)$',
                    page33_text, re.MULTILINE
                )
                if at1_match:
                    tlac1["at1"] = parse_number(at1_match.group(1), european=False) * 1_000_000
                else:
                    raise ValueError("Could not extract at1")

                # Pattern: "6 Tier 2 capital (T2) 7,648"
                tier2_match = re.search(
                    r'^6\s+Tier 2 capital \(T2\)\s+(\d+[.,]\d+)$',
                    page33_text, re.MULTILINE
                )
                if tier2_match:
                    tlac1["tier2"] = parse_number(tier2_match.group(1), european=False) * 1_000_000
                else:
                    raise ValueError("Could not extract tier2")

                # === KM2 RATIOS (SOFT TIER) ===
                # Pattern: "3 Own Funds and eligible liabilities as a percentage of TREA 30.59%"
                mrel_pct_trea_match = re.search(
                    r'^3\s+Own Funds and eligible liabilities as a percentage of TREA\s+([\d.,]+%)$',
                    page33_text, re.MULTILINE
                )
                if mrel_pct_trea_match:
                    val = parse_number(mrel_pct_trea_match.group(1), european=False)
                    if val is not None:
                        km2["mrel_pct_trea"] = val / 100.0

                # Pattern: "EU-3a of which Own Funds and subordinated liabilities 22.71%"
                subord_pct_trea_match = re.search(
                    r'^EU-3a\s+of which Own Funds and subordinated liabilities\s+([\d.,]+%)$',
                    page33_text, re.MULTILINE
                )
                if subord_pct_trea_match:
                    val = parse_number(subord_pct_trea_match.group(1), european=False)
                    if val is not None:
                        km2["subord_pct_trea"] = val / 100.0

                # Pattern: "5 Own Funds and eligible liabilities as percentage of the TEM 10.00%"
                mrel_pct_tem_match = re.search(
                    r'^5\s+Own Funds and eligible liabilities as percentage of the TEM\s+([\d.,]+%)$',
                    page33_text, re.MULTILINE
                )
                if mrel_pct_tem_match:
                    val = parse_number(mrel_pct_tem_match.group(1), european=False)
                    if val is not None:
                        km2["mrel_pct_tem"] = val / 100.0

                # Pattern: "EU-5a of which Own Funds or subordinated liabilities 7.42%"
                subord_pct_tem_match = re.search(
                    r'^EU-5a\s+of which Own Funds or subordinated liabilities\s+([\d.,]+%)$',
                    page33_text, re.MULTILINE
                )
                if subord_pct_tem_match:
                    val = parse_number(subord_pct_tem_match.group(1), european=False)
                    if val is not None:
                        km2["subord_pct_tem"] = val / 100.0

                # === MREL REQUIREMENTS (SOFT TIER) ===
                # Pattern: "EU-7 MREL expressed as percentage of the TREA 27.05%"
                mrel_req_trea_match = re.search(
                    r'^EU-7\s+MREL expressed as percentage of the TREA\s+([\d.,]+%)$',
                    page33_text, re.MULTILINE
                )
                if mrel_req_trea_match:
                    val = parse_number(mrel_req_trea_match.group(1), european=False)
                    if val is not None:
                        km2["mrel_requirement_trea"] = val / 100.0

                # Pattern: "EU-8 of which to be met with Own Funds or subordinated liabilities 19.36%"
                mrel_subord_req_trea_match = re.search(
                    r'^EU-8\s+of which to be met with Own Funds or subordinated liabilities\s+([\d.,]+%)$',
                    page33_text, re.MULTILINE
                )
                if mrel_subord_req_trea_match:
                    val = parse_number(mrel_subord_req_trea_match.group(1), european=False)
                    if val is not None:
                        km2["mrel_subord_requirement_trea"] = val / 100.0

                # Pattern: "EU-9 MREL expressed as percentage of the TEM 5.98%"
                mrel_req_tem_match = re.search(
                    r'^EU-9\s+MREL expressed as percentage of the TEM\s+([\d.,]+%)$',
                    page33_text, re.MULTILINE
                )
                if mrel_req_tem_match:
                    val = parse_number(mrel_req_tem_match.group(1), european=False)
                    if val is not None:
                        km2["mrel_requirement_tem"] = val / 100.0

                # Pattern: "EU-10 of which to be met with Own Funds or subordinated liabilities 5.98%"
                mrel_subord_req_tem_match = re.search(
                    r'^EU-10\s+of which to be met with Own Funds or subordinated liabilities\s+([\d.,]+%)$',
                    page33_text, re.MULTILINE
                )
                if mrel_subord_req_tem_match:
                    val = parse_number(mrel_subord_req_tem_match.group(1), european=False)
                    if val is not None:
                        km2["mrel_subord_requirement_tem"] = val / 100.0

                # === TLAC1 COMPOSITION BREAKDOWN (SOFT TIER) ===
                # Pattern: "12 Eligible liabilities instruments issued directly... (B) 11,221"
                subord_own_match = re.search(
                    r'^12\s+Eligible liabilities.*?\(B\)\s+(\d+[.,]\d+)$',
                    page33_text, re.MULTILINE | re.DOTALL
                )
                if subord_own_match:
                    tlac1["subord_own_issuance"] = parse_number(subord_own_match.group(1), european=False) * 1_000_000

                # Pattern: "13 Eligible liabilities that are not subordinated... 24,275"
                senior_pre_cap_match = re.search(
                    r'^13\s+Eligible liabilities.*?\(not grandfathered pre cap\)\s+(\d+[.,]\d+)$',
                    page33_text, re.MULTILINE | re.DOTALL
                )
                if senior_pre_cap_match:
                    tlac1["senior_pre_cap"] = parse_number(senior_pre_cap_match.group(1), european=False) * 1_000_000

                # Pattern: "EU13a Eligible liabilities ... (pre-cap) 482"
                senior_grandfathered_match = re.search(
                    r'EU13a.*\(pre-cap\)\s+(\d+)$',
                    page33_text, re.MULTILINE
                )
                if senior_grandfathered_match:
                    tlac1["senior_grandfathered"] = parse_number(senior_grandfathered_match.group(1), european=False) * 1_000_000

        except Exception as e:
            raise ValueError(f"Failed to extract UniCredit PDF data: {e}")

        return cls._build_facts(per_date, entity_name=cls.meta.name)
