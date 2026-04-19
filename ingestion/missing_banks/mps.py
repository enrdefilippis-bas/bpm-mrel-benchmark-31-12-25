"""Banca Monte dei Paschi di Siena S.p.A. parser (manual-entry only)."""
from __future__ import annotations

from .base import BankMeta, BaseBankParser


class MPSParser(BaseBankParser):
    meta = BankMeta(
        lei="J4CP7MHCXR8DAQMKIL78",
        name="Banca Monte dei Paschi di Siena S.p.A.",
        country="Italy",
        source_tag="pdf-mps",
        pillar3_url_pattern="https://www.gruppomps.it/static/upload/pil/pillar3-report-december-{year}.pdf",
        ir_page="https://www.gruppomps.it/en/investor-relations/pillar-3.html",
    )
