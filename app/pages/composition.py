"""Composition page (Q2 + Q4) — stack composition by instrument class."""
from __future__ import annotations

import dash

from app.pages._placeholder import placeholder

dash.register_page(__name__, path="/composition", name="Composition", order=2)


def layout():
    return placeholder(
        "Composition — MREL stack by instrument class",
        "Stacked bars per bank: CET1 · AT1 · T2 · senior non-preferred · "
        "senior preferred. Toggle between 100% mix and €bn absolute, sort by "
        "any metric, BPM always highlighted.",
        phase="Phase 3",
    )
