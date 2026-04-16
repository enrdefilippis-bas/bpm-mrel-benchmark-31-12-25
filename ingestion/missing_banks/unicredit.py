"""UniCredit S.p.A. Pillar 3 parser."""
from __future__ import annotations

from core.schema import Source

from .base import BankMeta, BaseBankParser


class UniCreditParser(BaseBankParser):
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
