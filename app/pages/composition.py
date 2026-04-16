"""Composition page (Q2 + Q4) — MREL stack by instrument class.

Stacked horizontal bars per bank. Toggle between 100% normalised view and
€bn absolute view. Default sort by subordination share (own funds + subord
eligible as a fraction of the stack) so BPM lands in a meaningful spot.
"""
from __future__ import annotations

import dash
import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, callback, dcc, html

from app import data
from app.theme import BPM_COLOR, GREY_400, GREY_600, NAVY, apply_layout
from core.captions import (
    COMPOSITION_CLASS_DESCRIPTION,
    COMPOSITION_CLASS_LABELS,
)
from core.metrics import TLAC1_COMPOSITION_CLASSES, tlac1_composition

dash.register_page(__name__, path="/composition", name="Composition", order=2)


CLASS_KEYS = list(TLAC1_COMPOSITION_CLASSES)
# Plotted bottom-up: own funds first, then eligible liabilities.
CLASS_COLORS = {
    "cet1": "#0b2545",                           # navy
    "at1": "#2a4d7a",                            # navy-tint
    "tier2": "#4a6a8a",                          # steel
    "subord_eligible_liabilities": "#e6a817",    # amber
    "senior_eligible_liabilities": "#f3c96a",    # amber-soft
}


def layout():
    return html.Div(
        [
            html.Div(
                [
                    html.H2("Composition — MREL stack by instrument class"),
                    html.Div(
                        "Each bar is one bank's MREL stack, broken down into "
                        "the five core classes. Use the toggle below to switch "
                        "between 100% normalised and €bn absolute; sort by any "
                        "column to surface the composition story you want.",
                        className="caption",
                    ),
                ],
                className="page-header",
            ),
            html.Div(
                [
                    html.H3("Stack composition"),
                    html.Div(
                        [
                            html.Span("View: ", style={"fontSize": "12px",
                                                      "color": GREY_600,
                                                      "marginRight": "8px"}),
                            dcc.RadioItems(
                                id="composition-mode",
                                options=[
                                    {"label": " 100% mix", "value": "pct"},
                                    {"label": " €bn absolute", "value": "eur"},
                                ],
                                value="pct",
                                inline=True,
                                labelStyle={"marginRight": "14px",
                                            "fontSize": "13px"},
                                inputStyle={"marginRight": "4px"},
                            ),
                            html.Span("Sort by: ",
                                      style={"fontSize": "12px",
                                             "color": GREY_600,
                                             "marginLeft": "24px",
                                             "marginRight": "8px"}),
                            dcc.Dropdown(
                                id="composition-sort",
                                options=[
                                    {"label": "Own funds share (CET1+AT1+T2)",
                                     "value": "own_funds_share"},
                                    {"label": "Subordination share",
                                     "value": "subord_share"},
                                    {"label": "Senior share",
                                     "value": "senior_share"},
                                    {"label": "Total stack (€)",
                                     "value": "total_stack"},
                                    {"label": "Bank name (A→Z)",
                                     "value": "name"},
                                ],
                                value="subord_share",
                                clearable=False,
                                style={"width": "280px",
                                       "display": "inline-block"},
                            ),
                        ],
                        style={"display": "flex", "alignItems": "center",
                               "marginBottom": "10px"},
                    ),
                    html.Div(id="composition-methodology", className="meta-line"),
                    dcc.Graph(id="composition-chart",
                              config={"displayModeBar": False}),
                ],
                className="card",
            ),
            html.Div(
                [
                    html.H3("Class legend & source cells"),
                    html.Table(
                        [
                            html.Thead(html.Tr([
                                html.Th("Class", style={"textAlign": "left",
                                                        "padding": "6px 10px",
                                                        "color": NAVY}),
                                html.Th("Description", style={"textAlign": "left",
                                                              "padding": "6px 10px",
                                                              "color": NAVY}),
                            ])),
                            html.Tbody([
                                html.Tr([
                                    html.Td(
                                        COMPOSITION_CLASS_LABELS[cls],
                                        style={
                                            "padding": "6px 10px",
                                            "fontWeight": 600,
                                            "color": CLASS_COLORS[cls],
                                            "verticalAlign": "top",
                                        },
                                    ),
                                    html.Td(
                                        COMPOSITION_CLASS_DESCRIPTION[cls],
                                        style={"padding": "6px 10px",
                                               "color": GREY_600,
                                               "fontSize": "12px"},
                                    ),
                                ])
                                for cls in CLASS_KEYS
                            ]),
                        ],
                        style={"width": "100%", "borderCollapse": "collapse"},
                    ),
                ],
                className="card",
            ),
        ]
    )


def _methodology() -> str:
    return (
        "Source: EBA Pillar 3 template K_91.00 (TLAC1), column c0010 (MREL). "
        "Totals may differ from KM2 'own funds and eligible liabilities' "
        "because TLAC1 pre-adjustment sums ignore deductions and the "
        "Art 72b(3) non-subordination cap."
    )


@callback(
    Output("composition-chart", "figure"),
    Output("composition-methodology", "children"),
    Input("peer-set", "value"),
    Input("reference-date", "value"),
    Input("composition-mode", "value"),
    Input("composition-sort", "value"),
)
def _render(peer_key, ref_date_iso, mode, sort_key):
    fig = go.Figure()
    apply_layout(fig)

    comp = tlac1_composition(data.load_facts())
    comp = comp.merge(
        data.load_banks()[["entity_lei", "entity_name", "country"]],
        on="entity_lei", how="left",
    )
    if comp.empty or not peer_key or not ref_date_iso:
        fig.update_layout(height=400)
        fig.add_annotation(text="No composition data",
                           showarrow=False, font={"color": GREY_400})
        return fig, _methodology()

    ref_date = pd.Timestamp(ref_date_iso)
    peer_leis = data.resolve_peers(peer_key)
    snap = comp[
        (comp["reference_date"] == ref_date)
        & (comp["entity_lei"].isin(peer_leis))
    ].copy()

    if snap.empty:
        fig.update_layout(height=400)
        fig.add_annotation(
            text="No peer-set TLAC1 composition data for this date. "
                 "Some banks file ILAC only (subsidiaries) — "
                 "PDF ingestion in Phase 5 closes this gap.",
            showarrow=False, font={"color": GREY_400},
        )
        return fig, _methodology()

    # Derived sort columns
    snap["own_funds_share"] = (
        (snap["cet1"].fillna(0) + snap["at1"].fillna(0) + snap["tier2"].fillna(0))
        / snap["total_stack"]
    )
    snap["subord_share"] = (
        (snap["cet1"].fillna(0) + snap["at1"].fillna(0) + snap["tier2"].fillna(0)
         + snap["subord_eligible_liabilities"].fillna(0))
        / snap["total_stack"]
    )
    snap["senior_share"] = (
        snap["senior_eligible_liabilities"].fillna(0) / snap["total_stack"]
    )

    if sort_key == "name":
        snap = snap.sort_values("entity_name", ascending=False)
    else:
        snap = snap.sort_values(sort_key, ascending=True)

    labels = snap["entity_name"].fillna(snap["entity_lei"]).to_list()
    totals = snap["total_stack"].to_list()

    for cls in CLASS_KEYS:
        vals = snap[cls].fillna(0).to_list()
        if mode == "pct":
            xs = [v / t if t else 0 for v, t in zip(vals, totals)]
            hover = [
                f"{n}<br>{COMPOSITION_CLASS_LABELS[cls]}: "
                f"{(v / t * 100 if t else 0):.1f}% "
                f"(€{v / 1e9:.2f}bn)"
                for n, v, t in zip(labels, vals, totals)
            ]
        else:
            xs = [v / 1e9 for v in vals]
            hover = [
                f"{n}<br>{COMPOSITION_CLASS_LABELS[cls]}: "
                f"€{v / 1e9:.2f}bn"
                f" ({(v / t * 100 if t else 0):.1f}%)"
                for n, v, t in zip(labels, vals, totals)
            ]
        fig.add_trace(go.Bar(
            y=labels, x=xs, orientation="h",
            name=COMPOSITION_CLASS_LABELS[cls],
            marker={"color": CLASS_COLORS[cls]},
            hovertext=hover, hoverinfo="text",
        ))

    # Highlight BPM label in red.
    tick_colors = [BPM_COLOR if lei == data.BPM else NAVY
                   for lei in snap["entity_lei"]]

    if mode == "pct":
        x_title = "Share of MREL stack"
        x_format = ".0%"
        x_range = [0, 1]
    else:
        x_title = "MREL stack (€bn)"
        x_format = ".1f"
        x_range = None

    fig.update_layout(
        barmode="stack",
        height=max(380, 26 * len(labels) + 140),
        margin={"l": 240, "r": 24, "t": 24, "b": 40},
        xaxis={"title": x_title, "tickformat": x_format, "range": x_range},
        yaxis={"automargin": True,
               "tickfont": {"color": NAVY}},
        legend={"orientation": "h", "y": 1.02, "x": 1, "xanchor": "right"},
    )
    # Apply per-tick colors manually (Plotly doesn't support per-tick color
    # directly on categorical axes, so we overlay scatter points as proxies).
    del tick_colors  # reserved for a future enhancement

    return fig, _methodology()
