"""Banco BPM Pillar 3 parser.

BPM is in the EBA cell-level export, so KM2 and TLAC1 are sourced from
there. However, the EBA export for BPM TLAC3 (K_97.00) **aggregates Rank 2
and Rank 4 under a single 'no-open_key' line**, losing the granular split
between Capital instruments/Subordinated (Rank 2) and Senior Non-Preferred
Debt (Rank 4). The BPM Pillar 3 PDF presents the full breakdown.

This parser contributes ONLY the TLAC3 blocks (maturity + creditor
ranking) from the manual_entry JSON. Merge logic in ``ingestion/normalize``
gives manual_entries precedence over EBA for the TLAC3 template for this
specific bank.
"""
from __future__ import annotations

from .base import BankMeta, BaseBankParser
from core.schema import Source


class BPMParser(BaseBankParser):
    """Banco BPM Pillar 3 parser (TLAC3 override from PDF)."""

    meta = BankMeta(
        lei="815600E4E6DCD2D25E30",
        name="BANCO BPM SOCIETA' PER AZIONI",
        country="Italy",
        source_tag=Source.PDF_BPM.value,
        pillar3_url_pattern=(
            "https://gruppo.bancobpm.it/download/"
            "informativa-da-parte-degli-enti-al-pubblico-terzo-pilastro-"
            "del-gruppo-banco-bpm-dati-riferiti-al-{year}-{quarter}"
        ),
        ir_page="https://gruppo.bancobpm.it/en/investor-relations/pillar-3/",
    )
