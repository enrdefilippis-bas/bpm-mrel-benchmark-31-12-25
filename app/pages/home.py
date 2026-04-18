"""Home hub — 8 narrative tiles + hero distribution chart.

Each tile shows BPM's rank in the selected peer set for a headline metric
and links to the matching drill-down page. The hero chart shows BPM's
position in the full 113-bank distribution for a user-chosen metric.
"""
from __future__ import annotations

from typing import Final

import dash
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, callback, dcc, html

from app import data
from app.components.metric_tile import metric_tile
from app.components.tooltip import metric_methodology
from app.theme import (
    BPM_COLOR,
    GREY_400,
    GREY_600,
    NAVY,
    PEER_COLOR,
    STEEL,
    apply_layout,
)
from core.captions import METRIC_CAPTIONS, get_caption
from core.ranking import peer_summary, rank_in_peer_set


dash.register_page(__name__, path="/", name="Home", order=0)


# (metric_key, destination-page, highlight-flag)
TILE_SPECS: Final[list[tuple[str, str, bool]]] = [
    ("mrel_pct_trea", "/cushion", True),
    ("mrel_surplus_trea_pp", "/cushion", False),
    ("mrel_pct_tem", "/cushion", False),
    ("subord_pct_trea", "/composition", False),
    ("subordination_ratio", "/composition", False),
    ("mrel_requirement_trea", "/cushion", False),
    ("mrel_total_amount", "/composition", False),
    ("trea", "/outliers", False),
    ("total_assets", "/outliers", False),
    ("cet1_ratio", "/outliers", False),
    ("total_capital_ratio", "/outliers", False),
    ("leverage_ratio", "/outliers", False),
]


# Metrics the hero chart can plot.
HERO_METRIC_OPTIONS = [
    {"label": get_caption(k).label, "value": k}
    for k in ("mrel_pct_trea", "mrel_pct_tem", "subord_pct_trea",
              "mrel_surplus_trea_pp", "subordination_ratio",
              "cet1_ratio", "total_capital_ratio", "leverage_ratio", "total_assets")
]


def layout():
    return html.Div(
        [
            html.Div(
                [
                    html.H2("MREL capacity — BPM vs peers"),
                    html.Div(
                        "One screen, eight answers. Every tile ranks Banco BPM "
                        "against its selected peer set for a single analyst "
                        "question. Click any tile to drill down; the hero chart "
                        "shows BPM's position in the full 113-bank EU distribution.",
                        className="caption",
                    ),
                ],
                className="page-header",
            ),
            html.Div(id="home-tiles", className="tile-grid"),
            html.Div(
                [
                    html.Div(
                        [
                            html.H3("Hero distribution — full EU universe"),
                            html.Div(
                                [
                                    html.Span("Metric: ",
                                              style={"fontSize": "12px",
                                                     "color": GREY_600,
                                                     "marginRight": "6px"}),
                                    dcc.Dropdown(
                                        id="home-hero-metric",
                                        options=HERO_METRIC_OPTIONS,
                                        value="mrel_pct_trea",
                                        clearable=False,
                                        style={"width": "360px",
                                               "display": "inline-block"},
                                    ),
                                ],
                                style={"display": "flex", "alignItems": "center",
                                       "marginBottom": "4px"},
                            ),
                            html.Div(id="home-hero-caption", className="card-caption"),
                            dcc.Graph(id="home-hero-chart",
                                      config={"displayModeBar": False},
                                      style={"height": "380px"}),
                        ],
                        className="card",
                    ),
                ]
            ),
        ]
    )


@callback(
    Output("home-tiles", "children"),
    Input("peer-set", "value"),
    Input("reference-date", "value"),
)
def _render_tiles(peer_key: str, ref_date_iso: str):
    wide = data.load_km2()
    if wide.empty or not peer_key or not ref_date_iso:
        return [html.Div("No data ingested yet — run scripts/ingest.py.",
                         className="card")]
    ref_date = pd.Timestamp(ref_date_iso)
    snap = wide[wide["reference_date"] == ref_date]

    peer_leis = data.resolve_peers(peer_key)

    tiles = []
    for metric_key, href, highlight in TILE_SPECS:
        r = rank_in_peer_set(snap, metric_key, peer_leis, data.BPM,
                             ascending=False)
        stats = peer_summary(snap, metric_key, peer_leis)
        tiles.append(
            metric_tile(
                metric_key,
                href=href,
                rank=r.rank,
                total=r.total_with_data,
                value=r.value,
                peer_median=stats.get("median"),
                has_data=r.rank > 0,
                highlight=highlight,
            )
        )
    return tiles


@callback(
    Output("home-hero-chart", "figure"),
    Output("home-hero-caption", "children"),
    Input("home-hero-metric", "value"),
    Input("peer-set", "value"),
    Input("reference-date", "value"),
)
def _render_hero(metric_key: str, peer_key: str, ref_date_iso: str):
    wide = data.load_km2()
    caption = get_caption(metric_key)

    fig = go.Figure()
    apply_layout(fig)
    fig.update_layout(
        title=f"{caption.label} — 2025-12-31 snapshot",
        xaxis={"title": None, "showticklabels": False, "showgrid": False,
               "zeroline": False, "range": [-0.6, 0.6]},
        yaxis_title=caption.label,
        showlegend=False,
        height=380,
    )

    if wide.empty or not ref_date_iso:
        fig.add_annotation(text="No data", showarrow=False,
                           font={"color": GREY_400})
        return fig, "No ingested data yet."

    ref_date = pd.Timestamp(ref_date_iso)
    snap = wide[wide["reference_date"] == ref_date].dropna(subset=[metric_key])

    if snap.empty:
        fig.add_annotation(text=f"No data for {ref_date.date()}",
                           showarrow=False, font={"color": GREY_400})
        return fig, "No data for the selected reference date."

    peer_leis = set(data.resolve_peers(peer_key))
    values = snap[metric_key].to_numpy()
    names = snap["entity_name"].fillna(snap["entity_lei"]).to_numpy()
    leis = snap["entity_lei"].to_numpy()

    # Violin trace for the full universe shape.
    fig.add_trace(
        go.Violin(
            y=values, x=[0] * len(values),
            points=False, box_visible=True, meanline_visible=True,
            fillcolor="rgba(74, 106, 138, 0.12)",
            line_color=STEEL, opacity=0.9, name="Full universe",
            hoverinfo="skip",
        )
    )

    # Jittered dots for each bank, peers highlighted, BPM distinct.
    rng = np.random.default_rng(0)
    jitter = rng.uniform(-0.18, 0.18, size=len(values))

    is_bpm = leis == data.BPM
    is_peer = np.array([lei in peer_leis and lei != data.BPM for lei in leis])
    others = ~(is_bpm | is_peer)

    def _hover(metric_unit: str):
        if metric_unit == "%":
            return [f"{n}<br>{v * 100:.2f}%" for n, v in zip(names, values)]
        if metric_unit == "pp":
            return [f"{n}<br>{v * 100:.2f} pp" for n, v in zip(names, values)]
        if metric_unit == "€bn":
            return [f"{n}<br>€{v / 1e9:.1f}bn" for n, v in zip(names, values)]
        return [f"{n}<br>{v:.3f}" for n, v in zip(names, values)]

    hover = _hover(caption.unit)

    fig.add_trace(go.Scatter(
        x=np.where(others, 0 + jitter, None),
        y=np.where(others, values, None),
        mode="markers",
        marker={"size": 6, "color": GREY_400, "opacity": 0.6,
                "line": {"width": 0}},
        name="Other banks",
        text=hover, hovertemplate="%{text}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=np.where(is_peer, 0 + jitter, None),
        y=np.where(is_peer, values, None),
        mode="markers",
        marker={"size": 8, "color": PEER_COLOR, "opacity": 0.95,
                "line": {"width": 0.5, "color": NAVY}},
        name="Peer set",
        text=hover, hovertemplate="%{text}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=[0], y=values[is_bpm] if is_bpm.any() else [],
        mode="markers+text",
        marker={"size": 14, "color": BPM_COLOR, "symbol": "diamond",
                "line": {"width": 1.5, "color": "white"}},
        name="Banco BPM",
        text=["BPM"] if is_bpm.any() else [],
        textposition="middle right",
        textfont={"color": BPM_COLOR, "size": 12},
        hovertext=[n for n, b in zip(names, is_bpm) if b],
        hoverinfo="text",
    ))

    # Format y-axis according to unit
    if caption.unit in ("%", "pp"):
        fig.update_yaxes(tickformat=".0%")
    elif caption.unit == "€bn":
        fig.update_yaxes(tickprefix="€", ticksuffix="bn",
                         tickformat=".2s")

    methodology = metric_methodology(metric_key)
    return fig, methodology
