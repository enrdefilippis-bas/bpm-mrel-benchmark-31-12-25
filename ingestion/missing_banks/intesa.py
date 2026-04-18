"""Intesa Sanpaolo S.p.A. Pillar 3 parser."""
from __future__ import annotations

from pathlib import Path
import re

import pandas as pd
import pdfplumber

from core.schema import Source

from .base import BankMeta, BaseBankParser
from ._pdf_utils import parse_number


class IntesaParser(BaseBankParser):
    """Intesa Sanpaolo Pillar 3 parser.

    STRATEGY:
    - Page 18: EU OV1 table with CET1, Tier1, Total, TREA, TEM in Italian
    - Page 80: EU KM2 MREL table with headline metrics (MREL total, ratios)
    - Page 81: EU TLAC1 composition breakdown

    Number format: dots as thousands separators (e.g., 115.648 = 115,648 million).
    Amounts in EUR millions; multiply by 1M to get EUR.
    Tuned for 2025Q4 PDF layout; may need updating for future quarters.
    """

    meta = BankMeta(
        lei="2W8N8UU78PMDQKZENC08",
        name="Intesa Sanpaolo S.p.A.",
        country="Italy",
        source_tag=Source.PDF_INTESA.value,
        pillar3_url_pattern=(
            "https://group.intesasanpaolo.com/content/dam/portalgroup/repository-documenti/"
            "investor-relations/bilanci-relazioni/en/Pillar_3_Disclosure_{year}_{quarter}.pdf"
        ),
        ir_page=(
            "https://group.intesasanpaolo.com/en/investor-relations/"
            "financials/financial-reports"
        ),
    )

    @classmethod
    def parse_pdf(cls, pdf_path: Path | str) -> pd.DataFrame:
        """Extract KM2 and TLAC1 from Intesa PDF.

        KM2: Pages 18 and 80 have headline metrics. Page 18 has basic capital ratios,
        page 80 has KM2 metrics including MREL figures.

        TLAC1: Page 81 has composition breakdown.
        """
        pdf_path = Path(pdf_path)

        per_date = {"2025-12-31": {"km2": {}, "tlac1": {}}}
        km2 = per_date["2025-12-31"]["km2"]
        tlac1 = per_date["2025-12-31"]["tlac1"]

        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Page 18 (0-indexed page 17) for basic metrics (CET1, Tier1, Total, TREA, TEM)
                if len(pdf.pages) >= 18:
                    page18_text = pdf.pages[17].extract_text() or ""
                    lines18 = page18_text.split('\n')

                    for line in lines18:
                        line_stripped = line.strip()

                        # Row 1: CET1
                        if re.match(r'^1\s+Capitale primario', line_stripped):
                            # Format: "1 Capitale primario di classe 1 (CET1) 40.854 40.167 40.018 ..."
                            # Values are in millions EUR (European format with . as thousands sep)
                            match = re.search(r'CET1\)\s+(\d+[.,]\d+)', line_stripped)
                            if match:
                                tlac1["cet1"] = parse_number(match.group(1), european=True) * 1_000_000

                        # Row 4: TREA
                        if re.match(r'^4\s+Importo complessivo', line_stripped):
                            # Format: "4 Importo complessivo dell'esposizione al rischio 310.201 306.097 ..."
                            # Values are in millions EUR (European format)
                            match = re.search(r'rischio\s+(\d+[.,]\d+)', line_stripped)
                            if match:
                                km2["trea"] = parse_number(match.group(1), european=True) * 1_000_000

                        # Row 13: TEM (Leverage ratio exposure measure)
                        if re.match(r'^13\s+Misura dell', line_stripped):
                            # Format: "13 Misura dell'esposizione complessiva 831.920 824.144 ..."
                            # Values are in millions EUR (European format)
                            match = re.search(r'complessiva\s+(\d+[.,]\d+)', line_stripped)
                            if match:
                                km2["tem"] = parse_number(match.group(1), european=True) * 1_000_000

                # Page 80 (0-indexed page 79) for KM2 MREL table
                if len(pdf.pages) >= 80:
                    page80_text = pdf.pages[79].extract_text() or ""
                    lines80 = page80_text.split('\n')

                    for line in lines80:
                        line_stripped = line.strip()

                        # Row 1: MREL total amount
                        # Format: "1 Fondi Propri e passività ammissibili 115.648"
                        # Values in millions EUR (European format with . as thousands separator)
                        if re.match(r'^1\s+Fondi Propri e', line_stripped):
                            match = re.search(r'ammissibili\s+(\d+[.,]\d+)', line_stripped)
                            if match:
                                km2["mrel_total_amount"] = parse_number(match.group(1), european=True) * 1_000_000

                        # Row 3: MREL as % of TREA
                        # Format: "3 Fondi Propri e passività ammissibili in percentuale del TREA 37,28%"
                        if re.match(r'^3\s+Fondi Propri', line_stripped):
                            match = re.search(r'(\d+[.,]\d+)%', line_stripped)
                            if match:
                                km2["mrel_pct_trea"] = parse_number(match.group(1), european=True) / 100

                        # Row 5: MREL as % of TEM
                        # Format: "5 Fondi Propri e passività ammissibili in percentuale della TEM 13,90%"
                        if re.match(r'^5\s+Fondi Propri', line_stripped):
                            match = re.search(r'(\d+[.,]\d+)%', line_stripped)
                            if match:
                                km2["mrel_pct_tem"] = parse_number(match.group(1), european=True) / 100

                        # Row EU-3a: Subordinated as % of TREA
                        # Format: "EU-3a di cui fondi propri e passività subordinate 21,71%"
                        if re.match(r'^EU-3a', line_stripped):
                            match = re.search(r'(\d+[.,]\d+)%', line_stripped)
                            if match:
                                km2["subord_pct_trea"] = parse_number(match.group(1), european=True) / 100

                        # Row EU-5a: Subordinated as % of TEM
                        # Format: "EU-5a di cui fondi propri o passività subordinate 8,09%"
                        if re.match(r'^EU-5a', line_stripped):
                            match = re.search(r'(\d+[.,]\d+)%', line_stripped)
                            if match:
                                km2["subord_pct_tem"] = parse_number(match.group(1), european=True) / 100

                        # Row EU-7: MREL requirement as % of TREA
                        if re.match(r'^EU-7', line_stripped):
                            match = re.search(r'(\d+[.,]\d+)%', line_stripped)
                            if match:
                                km2["mrel_requirement_trea"] = parse_number(match.group(1), european=True) / 100

                        # Row EU-8: Subordinated requirement as % of TREA
                        if re.match(r'^EU-8', line_stripped):
                            match = re.search(r'(\d+[.,]\d+)%', line_stripped)
                            if match:
                                km2["mrel_subord_requirement_trea"] = parse_number(match.group(1), european=True) / 100

                        # Row EU-9: MREL requirement as % of TEM
                        if re.match(r'^EU-9', line_stripped):
                            match = re.search(r'(\d+[.,]\d+)%', line_stripped)
                            if match:
                                km2["mrel_requirement_tem"] = parse_number(match.group(1), european=True) / 100

                        # Row EU-10: Subordinated requirement as % of TEM
                        if re.match(r'^EU-10', line_stripped):
                            match = re.search(r'(\d+[.,]\d+)%', line_stripped)
                            if match:
                                km2["mrel_subord_requirement_tem"] = parse_number(match.group(1), european=True) / 100

                # Page 81 (0-indexed page 80) for TLAC1 composition
                if len(pdf.pages) >= 81:
                    page81_text = pdf.pages[80].extract_text() or ""
                    lines81 = page81_text.split('\n')

                    for line in lines81:
                        line_stripped = line.strip()

                        # Row 2: AT1
                        if re.match(r'^2\s+Capitale aggiuntivo', line_stripped):
                            match = re.search(r'AT1\)\s+(\d+[.,]\d+)', line_stripped)
                            if match:
                                tlac1["at1"] = parse_number(match.group(1), european=True) * 1_000_000

                        # Row 6: Tier2
                        if re.match(r'^6\s+Capitale di classe 2', line_stripped):
                            match = re.search(r'T2\)\s+(\d+[.,]\d+)', line_stripped)
                            if match:
                                tlac1["tier2"] = parse_number(match.group(1), european=True) * 1_000_000

                        # Row 12: Subordinated own issuance
                        # Text: "12 passività escluse (non soggetti alla clausola grandfathering) 8.460"
                        if re.match(r'^12\s+passività escluse', line_stripped):
                            match = re.search(r'(\d+[.,]\d+)\s*$', line_stripped)
                            if match:
                                tlac1["subord_own_issuance"] = parse_number(match.group(1), european=True) * 1_000_000

                        # Row EU-12a: Subordinated intra-group
                        # Text: "EU-12a subordinati a passività escluse (non soggetti alla clausola grandfathering) -"
                        if re.match(r'^EU-12a', line_stripped):
                            match = re.search(r'(\d+[.,]\d+|-)\s*$', line_stripped)
                            if match:
                                if match.group(1) == '-':
                                    tlac1["subord_intra_group"] = 0
                                else:
                                    tlac1["subord_intra_group"] = parse_number(match.group(1), european=True) * 1_000_000

                        # Row EU-12b: Subordinated grandfathered
                        # Text: "EU-12b (subordinati soggetti alla clausola grandfathering) -"
                        if re.match(r'^EU-12b', line_stripped):
                            match = re.search(r'(\d+[.,]\d+|-)\s*$', line_stripped)
                            if match:
                                if match.group(1) == '-':
                                    tlac1["subord_grandfathered"] = 0
                                else:
                                    tlac1["subord_grandfathered"] = parse_number(match.group(1), european=True) * 1_000_000

                        # Row EU-12c: Subordinated Tier2 residual
                        # Text: "EU-12c elementi di classe 2 1.013"
                        if re.match(r'^EU-12c', line_stripped):
                            match = re.search(r'(\d+[.,]\d+)\s*$', line_stripped)
                            if match:
                                tlac1["subord_t2_residual"] = parse_number(match.group(1), european=True) * 1_000_000

                        # Row 13: Senior pre-TLAC (pre-TLAC eligible)
                        # Text: "13 massimale) 48.281"
                        # Previous full text: "Passività ammissibili non subordinate a passività escluse (non soggette alla clausola grandfathering pre-massimale) 48.281"
                        if re.match(r'^13\s+massimale', line_stripped):
                            match = re.search(r'(\d+[.,]\d+)\s*$', line_stripped)
                            if match:
                                tlac1["senior_pre_cap"] = parse_number(match.group(1), european=True) * 1_000_000

                        # Row EU-13a: Senior grandfathered (pre-TLAC eligible grandfathered)
                        # Text: "EU-13a massimale) 30"
                        if re.match(r'^EU-13a\s+massimale', line_stripped):
                            match = re.search(r'(\d+)\s*$', line_stripped)
                            if match:
                                tlac1["senior_grandfathered"] = parse_number(match.group(1), european=True) * 1_000_000

                    # Senior post-TLAC cap (0160) - not explicitly shown in Intesa composition, set to 0
                    tlac1["senior_post_cap"] = 0

        except Exception as e:
            raise ValueError(f"Failed to extract Intesa PDF data: {e}")

        # Check we have minimum required fields
        if not km2.get("mrel_total_amount") or not km2.get("trea") or not km2.get("tem"):
            raise ValueError("Could not extract required KM2 values (mrel_total_amount, trea, tem)")

        if not tlac1.get("cet1"):
            raise ValueError("Could not extract required TLAC1 value (cet1)")

        return cls._build_facts(per_date, entity_name=cls.meta.name)
