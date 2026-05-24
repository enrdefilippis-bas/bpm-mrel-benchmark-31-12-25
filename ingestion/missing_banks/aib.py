"""AIB Group plc Pillar 3 parser.

Added for the CdA presentation peer set (Cluster 2, Eurozone, similar size).
AIB publishes a quarterly Pillar 3 PDF. We bootstrap with manual entries
for KM2, TLAC1 and TLAC3 (maturity ladder + creditor ranking on the
resolution entity, even though AIB calls the template "TLAC3b" — same
scope as K_97.00 in the EBA cell schema).
"""
from __future__ import annotations

from .base import BankMeta, BaseBankParser
from core.schema import Source


class AIBParser(BaseBankParser):
    """AIB Group plc Pillar 3 parser (manual-entry only at this stage)."""

    meta = BankMeta(
        lei="635400AKJBGNS5WNQL34",
        name="AIB Group plc",
        country="Ireland",
        source_tag=Source.PDF_AIB.value,
        pillar3_url_pattern=(
            "https://aib.ie/content/dam/frontdoor/investorrelations/docs/"
            "resultscentre/pillar3/AIB-Group-plc-Q{quarter}-{year}-Pillar-3-Disclosures.pdf"
        ),
        ir_page=(
            "https://aib.ie/investorrelations/financial-information/"
            "results-centre"
        ),
    )
