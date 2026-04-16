"""Intesa Sanpaolo S.p.A. Pillar 3 parser."""
from __future__ import annotations

from core.schema import Source

from .base import BankMeta, BaseBankParser


class IntesaParser(BaseBankParser):
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
