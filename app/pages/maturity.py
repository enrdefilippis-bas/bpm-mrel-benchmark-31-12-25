"""Maturity page (Q3) — residual-maturity heatmap."""
from __future__ import annotations

import dash

from app.pages._placeholder import placeholder

dash.register_page(__name__, path="/maturity", name="Maturity", order=3)


def layout():
    return placeholder(
        "Maturity — residual-maturity profile",
        "Heatmap: banks × maturity buckets (<1y, 1–2y, 2–5y, 5–10y, 10y+, "
        "perpetual). Shade = % of stack. Default sort by <2y share to surface "
        "refi-wall risk first; BPM row pinned to the top.",
        phase="Phase 3",
    )
