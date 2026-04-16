"""Outliers page (Q8) — full 113-bank distribution explorer."""
from __future__ import annotations

import dash
import numpy as np
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
    STEEL,
    apply_layout,
)
from core.captions import get_caption

dash.register_page(__name__, path="/outliers", name="Outliers", order=7)


METRIC_OPTIONS = [
    {"label": "MREL % TREA", "value": "mrel_pct_trea"},
    {"label": "MREL % TEM", "value": "mrel_pct_tem"},
    {"label": "Subord % TREA", "value": "subord_pct_trea"},
    {"label": "Surplus TREA (pp)", "value": "mrel_surplus_trea_pp"},
    {"label": "Subordination ratio", "value": "subordination_ratio"},
    {"label": "MREL requirement % TREA", "value": "mrel_requirement_trea"},
]


def layout():
    return html.Div(
        [
            html.Div(
                [
                    html.H2("Outliers — full EU universe explorer"),
                    html.Div(
                        "Every bank in the Pillar 3 release plotted at once. "
                        "Left chart: distribution of a chosen metric with each "
                        "bank as a jittered dot (BPM = red diamond, peers = "
                        "steel-blue, others = grey). Right: 2-D scatter of "
                        "capacity vs subordination. Hover any dot for the "
                        "bank name and values.",
                        className="caption",
                    ),
                ],
                className="page-header",
            ),
            html.Div(
                [
                    html.Div(
                        [
                            html.H3("Distribution — full EU universe"),
                            html.Div(
                                [
                                    html.Span("Metric: ",
                                              style={"fontSize": "12px",
                                                     "color": GREY_600,
                                                     "marginRight": "8px"}),
                                    dcc.Dropdown(
                                        id="outliers-metric",
                                        options=METRIC_OPTIONS,
                                        value="mrel_pct_trea",
                                        clearable=False,
                                        style={"width": "260px"},
                                    ),
                                ],
                                style={"display": "flex",
                                       "alignItems": "center",
                                       "marginBottom": "10px"},
                            ),
                            html.Div(id="outliers-methodology",
                                     className="meta-line"),
                            dcc.Graph(id="outliers-violin",
                                      config={"displayModeBar": False},
                                      style={"height": "520px"}),
                        ],
                        className="card",
                        style={"flex": "1"},
                    ),
                    html.Div(
                        [
                            html.H3("Capacity vs subordination"),
                            html.Div(
                                "MREL % TREA on the x-axis, subord % TREA on "
                                "the y-axis. Banks above the diagonal are "
                                "more subordinated than average; BPM is the "
                                "red diamond.",
                                className="meta-line",
                            ),
                            dcc.Graph(id="outliers-scatter",
                                      config={"displayModeBar": False},
                                      style={"height": "520px"}),
                        ],
                        className="card",
                        style={"flex": "1"},
                    ),
                ],
                style={"display": "flex", "gap": "16px", "flexWrap": "wrap"},
            ),
        ]
    )


def _format_hover(unit: str, names, values):
    if unit == "%":
        return [f"{n}<br>{v * 100:.2f}%" for n, v in zip(names, values)]
    if unit == "pp":
        return [f"{n}<br>{v * 100:+.2f} pp" for n, v in zip(names, values)]
    if unit == "€bn":
        return [f"{n}<br>€{v / 1e9:.1f}bn" for n, v in zip(names, values)]
    return [f"{n}<br>{v:.3f}" for n, v in zip(names, values)]


@callback(
    Output("outliers-violin", "figure"),
    Output("outliers-scatter", "figure"),
    Output("outliers-methodology", "children"),
    Input("outliers-metric", "value"),
    Input("peer-set", "value"),
    Input("reference-date", "value"),
)
def _render(metric_key, peer_key, ref_date_iso):
    violin = go.Figure()
    scatter = go.Figure()
    apply_layout(violin)
    apply_layout(scatter)
    caption = get_caption(metric_key)

    wide = data.load_km2()
    if wide.empty or not ref_date_iso:
        for f in (violin, scatter):
            f.update_layout(height=520)
            f.add_annotation(text="No data", showarrow=False,
                             font={"color": GREY_400})
        return violin, scatter, metric_methodology(metric_key)

    ref_date = pd.Timestamp(ref_date_iso)
    snap = wide[wide["reference_date"] == ref_date].copy()
    peer_leis = set(data.resolve_peers(peer_key))

    # ---- Violin + jittered dots ----
    v_snap = snap.dropna(subset=[metric_key])
    if v_snap.empty:
        violin.update_layout(height=520)
        violin.add_annotation(text=f"No data for {ref_date.date()}",
                              showarrow=False, font={"color": GREY_400})
    else:
        values = v_snap[metric_key].to_numpy()
        names = v_snap["entity_name"].fillna(v_snap["entity_lei"]).to_numpy()
        leis = v_snap["entity_lei"].to_numpy()
        is_bpm = leis == data.BPM
        is_peer = np.array([l in peer_leis and l != data.BPM for l in leis])
        others = ~(is_bpm | is_peer)

        rng = np.random.default_rng(1)
        jitter = rng.uniform(-0.2, 0.2, size=len(values))

        violin.add_trace(go.Violin(
            y=values, x=[0] * len(values),
            points=False, box_visible=True, meanline_visible=True,
            fillcolor="rgba(74, 106, 138, 0.10)",
            line_color=STEEL, opacity=0.9, name="Distribution",
            hoverinfo="skip",
        ))

        hover = _format_hover(caption.unit, names, values)
        violin.add_trace(go.Scatter(
            x=np.where(others, jitter, None),
            y=np.where(others, values, None),
            mode="markers",
            marker={"size": 6, "color": GREY_400, "opacity": 0.55},
            name="Other banks",
            text=hover, hovertemplate="%{text}<extra></extra>",
        ))
        violin.add_trace(go.Scatter(
            x=np.where(is_peer, jitter, None),
            y=np.where(is_peer, values, None),
            mode="markers",
            marker={"size": 9, "color": PEER_COLOR, "opacity": 0.95,
                    "line": {"width": 0.5, "color": NAVY}},
            name="Peer set",
            text=hover, hovertemplate="%{text}<extra></extra>",
        ))
        if is_bpm.any():
            violin.add_trace(go.Scatter(
                x=[0], y=values[is_bpm],
                mode="markers+text",
                marker={"size": 14, "color": BPM_COLOR,
                        "symbol": "diamond",
                        "line": {"width": 1.5, "color": "white"}},
                name="Banco BPM",
                text=["BPM"], textposition="middle right",
                textfont={"color": BPM_COLOR, "size": 12},
                hovertext=[n for n, b in zip(names, is_bpm) if b],
                hoverinfo="text",
            ))

        if caption.unit in ("%", "pp"):
            violin.update_yaxes(tickformat=".0%")
        elif caption.unit == "€bn":
            violin.update_yaxes(tickprefix="€", ticksuffix="bn",
                                tickformat=".2s")
        violin.update_layout(
            height=520,
            xaxis={"title": None, "showticklabels": False, "showgrid": False,
                   "zeroline": False, "range": [-0.6, 0.6]},
            yaxis_title=caption.label,
            showlegend=True,
            legend={"orientation": "h", "y": 1.05, "x": 1, "xanchor": "right"},
        )

    # ---- Capacity vs subordination scatter ----
    s_snap = snap.dropna(subset=["mrel_pct_trea", "subord_pct_trea"]).copy()
    if s_snap.empty:
        scatter.update_layout(height=520)
        scatter.add_annotation(text=f"No scatter data for {ref_date.date()}",
                               showarrow=False, font={"color": GREY_400})
    else:
        leis = s_snap["entity_lei"].to_numpy()
        names = s_snap["entity_name"].fillna(s_snap["entity_lei"]).to_numpy()
        mrel = s_snap["mrel_pct_trea"].to_numpy()
        subord = s_snap["subord_pct_trea"].to_numpy()
        is_bpm = leis == data.BPM
        is_peer = np.array([l in peer_leis and l != data.BPM for l in leis])
        others = ~(is_bpm | is_peer)

        scatter_hover = [
            f"{n}<br>MREL % TREA: {m * 100:.2f}%<br>"
            f"Subord % TREA: {s * 100:.2f}%"
            for n, m, s in zip(names, mrel, subord)
        ]

        scatter.add_trace(go.Scatter(
            x=mrel[others], y=subord[others],
            mode="markers",
            marker={"size": 7, "color": GREY_400, "opacity": 0.55},
            name="Other banks",
            text=[h for h, o in zip(scatter_hover, others) if o],
            hovertemplate="%{text}<extra></extra>",
        ))
        scatter.add_trace(go.Scatter(
            x=mrel[is_peer], y=subord[is_peer],
            mode="markers",
            marker={"size": 10, "color": PEER_COLOR, "opacity": 0.95,
                    "line": {"width": 0.5, "color": NAVY}},
            name="Peer set",
            text=[h for h, p in zip(scatter_hover, is_peer) if p],
            hovertemplate="%{text}<extra></extra>",
        ))
        if is_bpm.any():
            scatter.add_trace(go.Scatter(
                x=mrel[is_bpm], y=subord[is_bpm],
                mode="markers+text",
                marker={"size": 14, "color": BPM_COLOR,
                        "symbol": "diamond",
                        "line": {"width": 1.5, "color": "white"}},
                name="Banco BPM",
                text=["BPM"], textposition="top right",
                textfont={"color": BPM_COLOR, "size": 12},
                hovertext=[n for n, b in zip(names, is_bpm) if b],
                hoverinfo="text",
            ))

        # Diagonal reference y = x
        lo = float(min(mrel.min(), subord.min()))
        hi = float(max(mrel.max(), subord.max()))
        scatter.add_trace(go.Scatter(
            x=[lo, hi], y=[lo, hi],
            mode="lines",
            line={"dash": "dot", "width": 1, "color": GREY_400},
            name="y = x", hoverinfo="skip",
        ))
        scatter.update_layout(
            height=520,
            xaxis={"title": "MREL % TREA", "tickformat": ".0%"},
            yaxis={"title": "Subord % TREA", "tickformat": ".0%"},
            legend={"orientation": "h", "y": 1.05, "x": 1, "xanchor": "right"},
        )

    return violin, scatter, metric_methodology(metric_key)
