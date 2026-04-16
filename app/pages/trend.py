"""Trend page (Q5) — multi-line time series across reference dates."""
from __future__ import annotations

import dash
import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, callback, dcc, html

from app import data
from app.components.tooltip import metric_methodology
from app.theme import (
    BPM_COLOR,
    GREY_400,
    GREY_600,
    NAVY,
    PEER_COLOR,
    REQUIREMENT_COLOR,
    apply_layout,
)
from core.captions import get_caption

dash.register_page(__name__, path="/trend", name="Trend", order=4)


TREND_METRICS = [
    {"label": "MREL % TREA", "value": "mrel_pct_trea"},
    {"label": "MREL % TEM", "value": "mrel_pct_tem"},
    {"label": "Subord % TREA", "value": "subord_pct_trea"},
    {"label": "Surplus TREA (pp)", "value": "mrel_surplus_trea_pp"},
    {"label": "Subordination ratio", "value": "subordination_ratio"},
    {"label": "MREL stack (€bn)", "value": "mrel_total_amount"},
]


def layout():
    return html.Div(
        [
            html.Div(
                [
                    html.H2("Trend — MREL metrics across 2025Q2 / Q3 / Q4"),
                    html.Div(
                        "One chart per peer bank showing the chosen metric "
                        "across the three reference dates in the current "
                        "Pillar 3 release. BPM bold; peers thin; the binding "
                        "MREL requirement (where applicable) drawn as an "
                        "amber dashed line.",
                        className="caption",
                    ),
                ],
                className="page-header",
            ),
            html.Div(
                [
                    html.H3("Quarterly trend"),
                    html.Div(
                        [
                            html.Span("Metric: ",
                                      style={"fontSize": "12px",
                                             "color": GREY_600,
                                             "marginRight": "8px"}),
                            dcc.Dropdown(
                                id="trend-metric",
                                options=TREND_METRICS,
                                value="mrel_pct_trea",
                                clearable=False,
                                style={"width": "280px",
                                       "display": "inline-block"},
                            ),
                        ],
                        style={"display": "flex", "alignItems": "center",
                               "marginBottom": "10px"},
                    ),
                    html.Div(id="trend-methodology", className="meta-line"),
                    dcc.Graph(id="trend-chart",
                              config={"displayModeBar": False},
                              style={"height": "520px"}),
                ],
                className="card",
            ),
        ]
    )


def _value_format(unit: str):
    if unit == "%":
        return lambda v: f"{v * 100:.2f}%"
    if unit == "pp":
        return lambda v: f"{v * 100:+.2f} pp"
    if unit == "€bn":
        return lambda v: f"€{v / 1e9:.1f}bn"
    return lambda v: f"{v:.3f}"


@callback(
    Output("trend-chart", "figure"),
    Output("trend-methodology", "children"),
    Input("peer-set", "value"),
    Input("trend-metric", "value"),
)
def _render(peer_key, metric_key):
    fig = go.Figure()
    apply_layout(fig)
    caption = get_caption(metric_key)

    wide = data.load_km2()
    if wide.empty or not peer_key or metric_key not in wide.columns:
        fig.update_layout(height=520)
        fig.add_annotation(text="No data", showarrow=False,
                           font={"color": GREY_400})
        return fig, metric_methodology(metric_key)

    peer_leis = data.resolve_peers(peer_key)
    snap = wide[wide["entity_lei"].isin(peer_leis)].copy()
    snap = snap.dropna(subset=[metric_key])

    if snap.empty:
        fig.update_layout(height=520)
        fig.add_annotation(text="No peer trend data",
                           showarrow=False, font={"color": GREY_400})
        return fig, metric_methodology(metric_key)

    fmt = _value_format(caption.unit)

    # Peer lines
    for lei, g in snap.groupby("entity_lei", sort=False):
        if lei == data.BPM:
            continue
        name = g["entity_name"].dropna().iloc[0] if not g["entity_name"].dropna().empty else lei
        g = g.sort_values("reference_date")
        fig.add_trace(go.Scatter(
            x=g["reference_date"], y=g[metric_key],
            mode="lines+markers",
            name=name,
            line={"color": PEER_COLOR, "width": 1.4},
            marker={"size": 6, "color": PEER_COLOR},
            opacity=0.75,
            hovertext=[f"{name}<br>{pd.Timestamp(d).date()}: {fmt(v)}"
                       for d, v in zip(g["reference_date"], g[metric_key])],
            hoverinfo="text",
        ))

    # BPM line on top
    bpm = snap[snap["entity_lei"] == data.BPM].sort_values("reference_date")
    if not bpm.empty:
        fig.add_trace(go.Scatter(
            x=bpm["reference_date"], y=bpm[metric_key],
            mode="lines+markers+text",
            name="Banco BPM",
            line={"color": BPM_COLOR, "width": 3},
            marker={"size": 10, "color": BPM_COLOR, "symbol": "diamond"},
            text=[None] * (len(bpm) - 1) + ["BPM"],
            textposition="middle right",
            textfont={"color": BPM_COLOR, "size": 12},
            hovertext=[f"BPM<br>{pd.Timestamp(d).date()}: {fmt(v)}"
                       for d, v in zip(bpm["reference_date"], bpm[metric_key])],
            hoverinfo="text",
        ))

    # Overlay the MREL requirement as a dashed amber line (only for the
    # headline TREA / TEM ratios where the requirement is comparable).
    req_col = {
        "mrel_pct_trea": "mrel_requirement_trea",
        "mrel_pct_tem": "mrel_requirement_tem",
    }.get(metric_key)
    if req_col and req_col in bpm.columns and not bpm.empty:
        req = bpm.dropna(subset=[req_col])
        if not req.empty:
            fig.add_trace(go.Scatter(
                x=req["reference_date"], y=req[req_col],
                mode="lines+markers",
                name="BPM requirement",
                line={"color": REQUIREMENT_COLOR, "width": 2, "dash": "dash"},
                marker={"size": 6, "color": REQUIREMENT_COLOR, "symbol": "x"},
                hovertemplate=f"BPM requirement<br>%{{x|%Y-%m-%d}}: "
                              + f"%{{y:.2%}}<extra></extra>",
            ))

    if caption.unit in ("%", "pp"):
        fig.update_yaxes(tickformat=".0%")
    elif caption.unit == "€bn":
        fig.update_yaxes(tickprefix="€", ticksuffix="bn", tickformat=".2s")

    fig.update_layout(
        height=520,
        xaxis={"title": "Reference date", "tickformat": "%Y-%m-%d"},
        yaxis={"title": caption.label},
        legend={"orientation": "v", "y": 1.0, "x": 1.02},
        margin={"l": 80, "r": 160, "t": 24, "b": 40},
    )
    return fig, metric_methodology(metric_key)
