"""Credito Emiliano Holding S.p.A. parser (manual-entry only)."""
from __future__ import annotations

from .base import BankMeta, BaseBankParser


class CredemParser(BaseBankParser):
    meta = BankMeta(
        lei="815600AD83B2B6317788",
        name="CREDITO EMILIANO HOLDING SOCIETA' PER AZIONI",
        country="Italy",
        source_tag="pdf-credem",
        pillar3_url_pattern="https://www.credem.it/pillar3",
        ir_page="https://www.credem.it/investor-relations",
    )
