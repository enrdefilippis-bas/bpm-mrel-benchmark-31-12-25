"""Trend page (Q5) — quarterly time series across the 3 reference dates."""
from __future__ import annotations

import dash

from app.pages._placeholder import placeholder

dash.register_page(__name__, path="/trend", name="Trend", order=4)


def layout():
    return placeholder(
        "Trend — MREL metrics across 2025Q2 / Q3 / Q4",
        "Multi-line time series of MREL % TREA, subord %, and surplus. BPM "
        "shown bold; peers thin; requirement line dashed.",
        phase="Phase 3",
    )
