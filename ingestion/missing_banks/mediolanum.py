"""Banca Mediolanum S.p.A. parser (manual-entry only)."""
from __future__ import annotations

from .base import BankMeta, BaseBankParser


class MediolanumParser(BaseBankParser):
    meta = BankMeta(
        lei="7LVZJ6XRIE7VNZ4UBX81",
        name="BANCA MEDIOLANUM S.P.A.",
        country="Italy",
        source_tag="pdf-mediolanum",
        pillar3_url_pattern="https://www.bancamediolanum.it/corporate/investors/bilanci",
        ir_page="https://www.bancamediolanum.it/corporate/investors/bilanci",
    )
