"""Creditor ranking page (Q6) — TLAC3 / TLAC3b insolvency rank."""
from __future__ import annotations

import dash

from app.pages._placeholder import placeholder

dash.register_page(__name__, path="/creditor-rank", name="Creditor rank", order=5)


def layout():
    return placeholder(
        "Creditor ranking — liabilities by insolvency rank",
        "Stacked horizontal bars per bank showing liabilities split by "
        "insolvency rank (K_97 TLAC3 for resolution entity, K_98 TLAC3b; "
        "K_95/96 for non-resolution entity). Toggle resolution scope.",
        phase="Phase 4",
    )
