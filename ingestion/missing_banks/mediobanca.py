"""Mediobanca - Banca di Credito Finanziario S.p.A. parser (manual-entry only)."""
from __future__ import annotations

from .base import BankMeta, BaseBankParser


class MediobancaParser(BaseBankParser):
    meta = BankMeta(
        lei="PSNL19R2RXX5U3QWHI44",
        name="Mediobanca - Banca di Credito Finanziario S.p.A.",
        country="Italy",
        source_tag="pdf-mediobanca",
        pillar3_url_pattern="https://www.mediobanca.com/static/upload_new/pil/pillar3_dicembre{year_short}_eng1.pdf",
        ir_page="https://www.mediobanca.com/en/investor-relations/pillar-3.html",
    )
