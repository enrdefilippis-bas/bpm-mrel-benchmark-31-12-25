"""Country page (Q7) — per-country aggregates."""
from __future__ import annotations

import dash

from app.pages._placeholder import placeholder

dash.register_page(__name__, path="/country", name="Country", order=6)


def layout():
    return placeholder(
        "Country — MREL distribution by jurisdiction",
        "Box plot per country for the chosen metric; median, IQR, outliers. "
        "Italy highlighted. Matches the SRB country-aggregate look.",
        phase="Phase 4",
    )
