"""BBVA S.A. Pillar 3 parser."""
from __future__ import annotations

from pathlib import Path
import re

import pandas as pd
import pdfplumber

from core.schema import Source

from .base import BankMeta, BaseBankParser
from ._pdf_utils import parse_number


class BBVAParser(BaseBankParser):
    """BBVA S.A. Pillar 3 parser.

    STRATEGY: 
    - Page 21 (or nearby) has KM2 EU KM2 table with MREL, TREA, TEM, ratios, requirements.
    - Page 60 (or nearby) has TLAC1 EU TLAC1 composition table.
    
    Number format: Anglo (59,277). Amounts in millions EUR;
    multiply by 1M to get EUR. Ratios as percentages (28.89% -> 0.2889).

    Tuned for 2025Q4 PDF layout; may need updating for future quarters.
    """

    meta = BankMeta(
        lei="U48ZC55EFS0K6YKA1212",
        name="Banco Bilbao Vizcaya Argentaria, S.A.",
        country="Spain",
        source_tag=Source.PDF_BBVA.value,
        pillar3_url_pattern=(
            "https://www.bbva.com/documents/{year}/pdf/"
            "bbva-pillar-3-report-{year}-english.pdf"
        ),
        ir_page=(
            "https://www.bbva.com/en/investors/"
        ),
    )

    # Window of pages to read (0-indexed). KM2 + requirements on ~page 21,
    # TLAC1 composition on ~page 60. A 440-page PDF takes ~30s to extract
    # in full; the narrow window reduces it to ~3s.
    _PAGE_WINDOW: tuple[int, int] = (15, 65)

    @classmethod
    def parse_pdf(cls, pdf_path: Path | str) -> pd.DataFrame:
        """Extract KM2 and TLAC1 from BBVA PDF.

        KM2: Page ~21 has EU KM2 table with MREL metrics.
        TLAC1: Page ~60 has EU TLAC1 composition table.
        Anglo format (59,277). Amounts in millions EUR.
        Ratios as percentages (28.89% -> 0.2889).
        """
        pdf_path = Path(pdf_path)

        per_date = {"2025-12-31": {"km2": {}, "tlac1": {}}}
        km2 = per_date["2025-12-31"]["km2"]
        tlac1 = per_date["2025-12-31"]["tlac1"]

        try:
            with pdfplumber.open(pdf_path) as pdf:
                start = max(0, cls._PAGE_WINDOW[0])
                end = min(len(pdf.pages), cls._PAGE_WINDOW[1])
                full_text = "\n".join(
                    (pdf.pages[i].extract_text() or "") for i in range(start, end)
                )

                # === KM2 TABLE (STRICT TIER) ===
                # Find "Own funds and eligible liabilities 59,277" line
                mrel_match = re.search(
                    r'^Own funds and eligible liabilities\s+(\d+[.,]\d+)',
                    full_text, re.MULTILINE
                )
                if mrel_match:
                    km2["mrel_total_amount"] = parse_number(mrel_match.group(1), european=False) * 1_000_000
                else:
                    raise ValueError("Could not extract mrel_total_amount")

                # Find "Total risk exposure amount of the resolution group (TREA) 205,154"
                trea_match = re.search(
                    r'Total risk exposure amount of the resolution group \(TREA\)\s+(\d+[.,]\d+)',
                    full_text, re.MULTILINE
                )
                if trea_match:
                    km2["trea"] = parse_number(trea_match.group(1), european=False) * 1_000_000
                else:
                    raise ValueError("Could not extract trea")

                # Find "Total exposure measure of the resolution group 580,788"
                tem_match = re.search(
                    r'Total exposure measure of the resolution group\s+(\d+[.,]\d+)',
                    full_text, re.MULTILINE
                )
                if tem_match:
                    km2["tem"] = parse_number(tem_match.group(1), european=False) * 1_000_000
                else:
                    raise ValueError("Could not extract tem")

                # === KM2 RATIOS (SOFT TIER) ===
                # Extract the "Own funds and eligible liabilities ratios" section
                ratios_section_match = re.search(
                    r'Own funds and eligible liabilities ratios and requirements(.*?)Minimum requirement for own funds',
                    full_text, re.DOTALL | re.MULTILINE
                )
                
                if ratios_section_match:
                    ratios_text = ratios_section_match.group(1)
                    
                    # "Own funds and eligible liabilities as a percentage of TREA 28.89 %"
                    mrel_pct_trea_match = re.search(
                        r'Own funds and eligible liabilities as a percentage of TREA\s+([\d.,]+\s*%)',
                        ratios_text, re.MULTILINE
                    )
                    if mrel_pct_trea_match:
                        val = parse_number(mrel_pct_trea_match.group(1), european=False)
                        if val is not None:
                            km2["mrel_pct_trea"] = val / 100.0

                    # Both subord rows use identical wording ("Of which own funds and
                    # subordinated liabilities"). Anchor each off the preceding TREA/TEM
                    # percentage row so we pick the right one.
                    subord_pct_trea_match = re.search(
                        r'Own funds and eligible liabilities as a percentage of TREA.*?\n'
                        r'Of which own funds and subordinated liabilities\s+(\d+[.,]\d+\s*%)',
                        ratios_text, re.DOTALL
                    )
                    if subord_pct_trea_match:
                        val = parse_number(subord_pct_trea_match.group(1), european=False)
                        if val is not None:
                            km2["subord_pct_trea"] = val / 100.0

                    # "Own funds and eligible liabilities as a percentage of the total exposure measure 10.21 %"
                    mrel_pct_tem_match = re.search(
                        r'Own funds and eligible liabilities as a percentage of the total exposure measure\s+([\d.,]+\s*%)',
                        ratios_text, re.MULTILINE
                    )
                    if mrel_pct_tem_match:
                        val = parse_number(mrel_pct_tem_match.group(1), european=False)
                        if val is not None:
                            km2["mrel_pct_tem"] = val / 100.0

                    # Anchor TEM subord off the preceding TEM percentage row.
                    subord_pct_tem_match = re.search(
                        r'Own funds and eligible liabilities as a percentage of the total exposure measure.*?\n'
                        r'Of which own funds and subordinated liabilities\s+(\d+[.,]\d+\s*%)',
                        ratios_text, re.DOTALL
                    )
                    if subord_pct_tem_match:
                        val = parse_number(subord_pct_tem_match.group(1), european=False)
                        if val is not None:
                            km2["subord_pct_tem"] = val / 100.0

                # === MREL REQUIREMENTS (SOFT TIER) ===
                # Extract the "Minimum requirement for own funds" section
                req_section_match = re.search(
                    r'Minimum requirement for own funds and eligible liabilities \(MREL\)(.*?)(?:The following sections|p\.\d+)',
                    full_text, re.DOTALL | re.MULTILINE
                )
                
                if req_section_match:
                    req_text = req_section_match.group(1)
                    
                    # "MREL requirement expressed as percentage of the total risk exposure amount 27.10 %"
                    mrel_req_trea_match = re.search(
                        r'MREL requirement expressed as percentage of the total risk exposure amount.*?(\d+[.,]\d+\s*%)',
                        req_text, re.MULTILINE | re.DOTALL
                    )
                    if mrel_req_trea_match:
                        val = parse_number(mrel_req_trea_match.group(1), european=False)
                        if val is not None:
                            km2["mrel_requirement_trea"] = val / 100.0

                    # "Of which own funds and subordinated liabilities (1) 17.47 %"
                    mrel_subord_req_trea_match = re.search(
                        r'^Of which own funds and subordinated liabilities \(\d\)\s+(\d+[.,]\d+\s*%)',
                        req_text, re.MULTILINE
                    )
                    if mrel_subord_req_trea_match:
                        val = parse_number(mrel_subord_req_trea_match.group(1), european=False)
                        if val is not None:
                            km2["mrel_subord_requirement_trea"] = val / 100.0

                    # "MREL requirement expressed as percentage of the total exposure measure 8.59 %"
                    mrel_req_tem_match = re.search(
                        r'MREL requirement expressed as percentage of the total exposure measure\s+(\d+[.,]\d+\s*%)',
                        req_text, re.MULTILINE
                    )
                    if mrel_req_tem_match:
                        val = parse_number(mrel_req_tem_match.group(1), european=False)
                        if val is not None:
                            km2["mrel_requirement_tem"] = val / 100.0

                    # Anchor TEM subord requirement off the preceding TEM req row.
                    mrel_subord_req_tem_match = re.search(
                        r'MREL requirement expressed as percentage of the total exposure measure.*?\n'
                        r'Of which own funds and subordinated liabilities\s+(\d+[.,]\d+\s*%)',
                        req_text, re.DOTALL
                    )
                    if mrel_subord_req_tem_match:
                        val = parse_number(mrel_subord_req_tem_match.group(1), european=False)
                        if val is not None:
                            km2["mrel_subord_requirement_tem"] = val / 100.0

                # === TLAC1 COMPOSITION (STRICT TIER) ===
                # "Common Equity Tier 1 capital (CET1) 31,053"
                cet1_match = re.search(
                    r'Common Equity Tier 1 capital \(CET1\)\s+(\d+[.,]\d+)',
                    full_text, re.MULTILINE
                )
                if cet1_match:
                    tlac1["cet1"] = parse_number(cet1_match.group(1), european=False) * 1_000_000
                else:
                    raise ValueError("Could not extract cet1")

                # "Additional Tier 1 capital (AT1) 5,303"
                at1_match = re.search(
                    r'Additional Tier 1 capital \(AT1\)\s+(\d+[.,]\d+)',
                    full_text, re.MULTILINE
                )
                if at1_match:
                    tlac1["at1"] = parse_number(at1_match.group(1), european=False) * 1_000_000
                else:
                    raise ValueError("Could not extract at1")

                # "Tier 2 capital (T2) 6,349"
                tier2_match = re.search(
                    r'Tier 2 capital \(T2\)\s+(\d+[.,]\d+)',
                    full_text, re.MULTILINE
                )
                if tier2_match:
                    tlac1["tier2"] = parse_number(tier2_match.group(1), european=False) * 1_000_000
                else:
                    raise ValueError("Could not extract tier2")

                # === TLAC1 COMPOSITION BREAKDOWN (SOFT TIER) ===
                # The PDF wraps long row labels so the amount sometimes lands
                # BETWEEN words of the row label, e.g.
                #   "subordinated to excluded liabilities (not\n6,739 6,067\ngrandfathered)"
                # So the regex has to accept the number interrupting the label.
                subord_own_match = re.search(
                    r'Eligible liabilities instruments issued directly by the resolution entity'
                    r'.*?subordinated to excluded liabilities \(not\s+'
                    r'([\d,]+)\s+[\d,—-]+\s+grandfathered\)',
                    full_text, re.DOTALL
                )
                if subord_own_match:
                    tlac1["subord_own_issuance"] = parse_number(subord_own_match.group(1), european=False) * 1_000_000

                # Same wrap pattern: number sits between "(subordinated" and "grandfathered)".
                subord_grand_match = re.search(
                    r'issued prior to 27 June 2019 \(subordinated\s+'
                    r'([\d,]+)\s+[\d,—-]+\s+grandfathered\)',
                    full_text, re.DOTALL
                )
                if subord_grand_match:
                    tlac1["subord_grandfathered"] = parse_number(subord_grand_match.group(1), european=False) * 1_000_000

                # "Tier 2 instruments with a residual maturity of at least one year to the extent they do not qualify as Tier 2 items 942"
                subord_t2_match = re.search(
                    r'Tier 2 instruments with a residual maturity of at least one year.*?do not qualify as Tier 2 items\s+(\d+)',
                    full_text, re.MULTILINE | re.DOTALL
                )
                if subord_t2_match:
                    tlac1["subord_t2_residual"] = parse_number(subord_t2_match.group(1), european=False) * 1_000_000

                # "Eligible liabilities that are not subordinated to excluded liabilities (not grandfathered pre cap) 8,637"
                senior_pre_cap_match = re.search(
                    r'Eligible liabilities that are not subordinated to excluded liabilities \(not grandfathered pre cap\)\s+(\d+[.,]\d+)',
                    full_text, re.MULTILINE
                )
                if senior_pre_cap_match:
                    tlac1["senior_pre_cap"] = parse_number(senior_pre_cap_match.group(1), european=False) * 1_000_000

                # "Eligible liabilities that are not subordinated to excluded liabilities issued prior to 27 June 2019 (pre-cap) 24"
                senior_grand_match = re.search(
                    r'issued prior to 27 June 2019 \(pre-cap\)\s+(\d+)(?:\s|$)',
                    full_text, re.MULTILINE
                )
                if senior_grand_match:
                    tlac1["senior_grandfathered"] = parse_number(senior_grand_match.group(1), european=False) * 1_000_000

        except Exception as e:
            raise ValueError(f"Failed to extract BBVA PDF data: {e}")

        return cls._build_facts(per_date, entity_name=cls.meta.name)
