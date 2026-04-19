"""BPER Banca S.p.A. parser (manual-entry only)."""
from __future__ import annotations

from .base import BankMeta, BaseBankParser


class BPERParser(BaseBankParser):
    meta = BankMeta(
        lei="N747OI7JINV7RUUH6190",
        name="BPER Banca S.p.A.",
        country="Italy",
        source_tag="pdf-bper",
        pillar3_url_pattern="https://group.bper.it/investor-relations/risultati-gruppo/pillar-3",
        ir_page="https://group.bper.it/investor-relations/risultati-gruppo/pillar-3",
    )
