"""Société Générale Pillar 3 parser."""
from __future__ import annotations

from core.schema import Source

from .base import BankMeta, BaseBankParser


class SocGenParser(BaseBankParser):
    meta = BankMeta(
        lei="O2RNE8IBXP4R0TD8PU41",
        name="Société Générale S.A.",
        country="France",
        source_tag=Source.PDF_SOCGEN.value,
        pillar3_url_pattern=(
            "https://www.societegenerale.com/sites/default/files/documents/{year}-"
            "{month:02d}/societe-generale-pillar-3-{year}-{quarter}.pdf"
        ),
        ir_page=(
            "https://www.societegenerale.com/en/investors/"
            "financial-results-and-publications"
        ),
    )
