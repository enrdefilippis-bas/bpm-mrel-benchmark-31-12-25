"""Banco Bilbao Vizcaya Argentaria (BBVA) Pillar 3 parser."""
from __future__ import annotations

from core.schema import Source

from .base import BankMeta, BaseBankParser


class BBVAParser(BaseBankParser):
    meta = BankMeta(
        lei="K8MS7FD7N5Z2WQ51AZ71",
        name="Banco Bilbao Vizcaya Argentaria, S.A.",
        country="Spain",
        source_tag=Source.PDF_BBVA.value,
        pillar3_url_pattern=(
            "https://shareholdersandinvestors.bbva.com/wp-content/uploads/{year}/"
            "{month:02d}/Pillar-III-{year}-{quarter}.pdf"
        ),
        ir_page=(
            "https://shareholdersandinvestors.bbva.com/financials/"
            "financial-reports/"
        ),
    )
