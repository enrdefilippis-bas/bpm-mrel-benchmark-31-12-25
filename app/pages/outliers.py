"""Outliers page (Q8) — full 113-bank distribution explorer."""
from __future__ import annotations

import dash

from app.pages._placeholder import placeholder

dash.register_page(__name__, path="/outliers", name="Outliers", order=7)


def layout():
    return placeholder(
        "Outliers — full EU universe explorer",
        "Violin plus jittered dots for every bank (BPM marked). Linked "
        "scatter of subord % vs MREL % TREA. Click any dot to cross-filter "
        "every other page to that bank.",
        phase="Phase 3",
    )
