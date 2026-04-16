"""Crédit Agricole S.A. Pillar 3 parser."""
from __future__ import annotations

from core.schema import Source

from .base import BankMeta, BaseBankParser


class CreditAgricoleParser(BaseBankParser):
    meta = BankMeta(
        lei="969500TJ5KRTCJQWXH05",
        name="Crédit Agricole S.A.",
        country="France",
        source_tag=Source.PDF_CREDIT_AGRICOLE.value,
        pillar3_url_pattern=(
            "https://www.credit-agricole.com/content/download/{doc_id}/file/"
            "CASA_Pillar_3_{year}_{quarter}.pdf"
        ),
        ir_page=(
            "https://www.credit-agricole.com/en/finance/"
            "financial-publications"
        ),
    )
