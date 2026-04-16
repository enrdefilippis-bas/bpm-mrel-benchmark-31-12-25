"""Self-documenting tooltip helpers.

Every metric displayed in the UI resolves its tooltip text through
`core.captions` so the formula and Pillar 3 source cell are always in sync
with the metric that's actually being shown.
"""
from __future__ import annotations

from dash import html

from core.captions import METRIC_CAPTIONS, get_caption


def metric_tooltip_text(metric_key: str) -> str:
    """One-line tooltip content: description + formula + sources."""
    if metric_key not in METRIC_CAPTIONS:
        return metric_key
    c = get_caption(metric_key)
    sources = " · ".join(c.sources)
    return f"{c.description}  ·  Formula: {c.formula}  ·  Source: {sources}"


def metric_help_icon(metric_key: str) -> html.Span:
    """Small 'ⓘ' glyph rendered with a browser-native tooltip."""
    return html.Span(
        "\u24d8",  # ⓘ
        title=metric_tooltip_text(metric_key),
        style={
            "color": "#9aa4b1",
            "marginLeft": "6px",
            "fontSize": "12px",
            "cursor": "help",
        },
    )


def metric_label(metric_key: str, bold: bool = False) -> html.Span:
    """Full metric label with inline help icon."""
    c = get_caption(metric_key)
    return html.Span(
        [
            html.Span(c.label, style={"fontWeight": 600 if bold else 400}),
            metric_help_icon(metric_key),
        ]
    )


def metric_methodology(metric_key: str) -> html.Div:
    """Block-level caption shown beneath chart titles.

    Spells out formula and source for readers who don't know to hover.
    """
    c = get_caption(metric_key)
    sources = " · ".join(c.sources)
    return html.Div(
        [
            html.Span(c.description, style={"color": "#5b6572"}),
            html.Br(),
            html.Span(f"Formula: {c.formula}", style={"color": "#5b6572"}),
            html.Span("  ·  ", style={"color": "#9aa4b1"}),
            html.Span(f"Source: {sources}", style={"color": "#5b6572"}),
        ],
        className="meta-line",
    )
