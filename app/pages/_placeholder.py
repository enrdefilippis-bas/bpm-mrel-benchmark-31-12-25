"""Shared 'coming in next phase' layout for pages not yet implemented."""
from __future__ import annotations

from dash import html


def placeholder(title: str, description: str, phase: str) -> html.Div:
    return html.Div(
        [
            html.Div(
                [html.H2(title), html.Div(description, className="caption")],
                className="page-header",
            ),
            html.Div(
                [
                    html.H3("Coming soon"),
                    html.Div(
                        f"This page will be built in {phase}. The Phase 1 data "
                        "layer already contains the facts it needs.",
                        className="card-caption",
                    ),
                ],
                className="card",
            ),
        ]
    )
