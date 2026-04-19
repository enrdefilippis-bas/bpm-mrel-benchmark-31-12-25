"""Cassa Centrale Banca S.p.A. parser (manual-entry only)."""
from __future__ import annotations

from .base import BankMeta, BaseBankParser


class CassaCentraleParser(BaseBankParser):
    meta = BankMeta(
        lei="LOO0AWXR8GF142JCO404",
        name="CASSA CENTRALE BANCA - CREDITO COOPERATIVO ITALIANO S.P.A.",
        country="Italy",
        source_tag="pdf-cassa-centrale",
        pillar3_url_pattern="https://www.cassacentrale.it/en/investors/pillar-3",
        ir_page="https://www.cassacentrale.it/en/investors/pillar-3",
    )
