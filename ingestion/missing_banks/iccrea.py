"""ICCREA Banca S.p.A. parser (manual-entry only)."""
from __future__ import annotations

from .base import BankMeta, BaseBankParser


class ICCREAParser(BaseBankParser):
    meta = BankMeta(
        lei="NNVPP80YIZGEY2314M97",
        name="ICCREA BANCA S.P.A.",
        country="Italy",
        source_tag="pdf-iccrea",
        pillar3_url_pattern="https://www.gruppobcciccrea.it/Pagine/Governance/Informativa-Pillar-III.aspx",
        ir_page="https://www.gruppobcciccrea.it/Pagine/Governance/Informativa-Pillar-III.aspx",
    )
