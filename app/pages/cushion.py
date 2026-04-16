"""Cushion page (Q1) — MREL capacity vs requirement across peer set.

Two horizontal bar charts (TREA basis and TEM basis), with the binding
MREL requirement drawn as a marker on each bar so the surplus/shortfall
reads at a glance. BPM is highlighted; peers ordered by capacity.
"""
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
from core.ranking import peer_summary, rank_in_peer_set


dash.register_page(__name__, path="/cushion", name="Cushion", order=1)


def layout():
    return html.Div(
        [
            html.Div(
                [
                    html.H2("Cushion — MREL capacity vs requirement"),
                    html.Div(
                        "Each bar shows a bank's MREL capacity; the amber marker "
                        "is the binding MREL requirement for that bank. Positive "
                        "gap = surplus; negative = shortfall. BPM is highlighted "
                        "in red.",
                        className="caption",
                    ),
                ],
                className="page-header",
            ),
            html.Div(id="cushion-badges",
                     style={"display": "flex", "gap": "12px",
                            "marginBottom": "16px"}),
            html.Div(
                [
                    html.H3("MREL as % of TREA"),
                    metric_methodology("mrel_pct_trea"),
                    dcc.Graph(id="cushion-trea-chart",
                              config={"displayModeBar": False},
                              style={"height": "620px"}),
                ],
                className="card",
            ),
            html.Div(
                [
                    html.H3("MREL as % of TEM"),
                    metric_methodology("mrel_pct_tem"),
                    dcc.Graph(id="cushion-tem-chart",
                              config={"displayModeBar": False},
                              style={"height": "620px"}),
                ],
                className="card",
            ),
        ]
    )


def _format_badge(title: str, value: str, sub: str, tone: str = "navy"):
    colors = {"navy": NAVY, "red": BPM_COLOR, "peer": PEER_COLOR}
    return html.Div(
        [
            html.Div(title, style={"color": GREY_600, "fontSize": "11px",
                                   "letterSpacing": "0.05em",
                                   "textTransform": "uppercase"}),
            html.Div(value, style={"color": colors.get(tone, NAVY),
                                   "fontSize": "22px", "fontWeight": 600}),
            html.Div(sub, style={"color": GREY_600, "fontSize": "12px"}),
        ],
        className="card",
        style={"flex": "1", "margin": "0"},
    )


def _cushion_figure(
    wide: pd.DataFrame,
    peer_leis: list[str],
    ref_date: pd.Timestamp,
    capacity_key: str,
    requirement_key: str,
) -> go.Figure:
    fig = go.Figure()
    apply_layout(fig)
    caption = get_caption(capacity_key)

    snap = wide[
        (wide["reference_date"] == ref_date)
        & (wide["entity_lei"].isin(peer_leis))
    ].dropna(subset=[capacity_key])

    if snap.empty:
        fig.add_annotation(text="No peer-set data for this date",
                           showarrow=False, font={"color": GREY_400})
        fig.update_layout(height=620, showlegend=False)
        return fig

    snap = snap.sort_values(capacity_key, ascending=True)
    labels = snap["entity_name"].fillna(snap["entity_lei"]).to_list()
    capacity = snap[capacity_key].to_list()
    requirement = snap[requirement_key].to_list() if requirement_key in snap.columns else [None] * len(snap)
    is_bpm = (snap["entity_lei"] == data.BPM).to_list()

    bar_colors = [BPM_COLOR if b else PEER_COLOR for b in is_bpm]
    capacity_hover = [
        f"{n}<br>Capacity: {c * 100:.2f}%"
        f"{('<br>Requirement: ' + f'{r * 100:.2f}%') if r is not None and pd.notna(r) else ''}"
        f"{('<br>Surplus: ' + f'{(c - r) * 100:+.2f} pp') if r is not None and pd.notna(r) else ''}"
        for n, c, r in zip(labels, capacity, requirement)
    ]

    fig.add_trace(go.Bar(
        y=labels, x=capacity,
        orientation="h",
        marker={"color": bar_colors},
        name=caption.short_label,
        hovertext=capacity_hover,
        hoverinfo="text",
    ))

    # Requirement markers
    req_labels = [n for n, r in zip(labels, requirement) if r is not None and pd.notna(r)]
    req_values = [r for r in requirement if r is not None and pd.notna(r)]
    if req_labels:
        fig.add_trace(go.Scatter(
            y=req_labels, x=req_values, mode="markers",
            marker={"symbol": "line-ns", "size": 18,
                    "line": {"color": REQUIREMENT_COLOR, "width": 3}},
            name="Requirement",
            hovertemplate="Requirement: %{x:.2%}<extra></extra>",
        ))

    fig.update_layout(
        xaxis={"tickformat": ".0%", "title": caption.label},
        yaxis={"automargin": True},
        showlegend=True,
        legend={"orientation": "h", "y": 1.02, "x": 1, "xanchor": "right"},
        height=max(380, 22 * len(labels) + 140),
        margin={"l": 220, "r": 24, "t": 48, "b": 40},
    )
    return fig


@callback(
    Output("cushion-badges", "children"),
    Output("cushion-trea-chart", "figure"),
    Output("cushion-tem-chart", "figure"),
    Input("peer-set", "value"),
    Input("reference-date", "value"),
)
def _render(peer_key: str, ref_date_iso: str):
    wide = data.load_km2()
    empty_fig = go.Figure()
    apply_layout(empty_fig)
    empty_fig.update_layout(height=620)

    if wide.empty or not peer_key or not ref_date_iso:
        return (
            [html.Div("No data ingested — run scripts/ingest.py.",
                      className="card")],
            empty_fig, empty_fig,
        )

    ref_date = pd.Timestamp(ref_date_iso)
    snap = wide[wide["reference_date"] == ref_date]
    peer_leis = data.resolve_peers(peer_key)

    # Rank badges (peer + universe) on the TREA metric.
    r_peer = rank_in_peer_set(snap, "mrel_pct_trea", peer_leis, data.BPM, ascending=False)
    universe_leis = snap["entity_lei"].dropna().unique().tolist()
    r_univ = rank_in_peer_set(snap, "mrel_pct_trea", universe_leis, data.BPM, ascending=False)
    stats = peer_summary(snap, "mrel_pct_trea", peer_leis)

    if r_peer.value is not None:
        bpm_value_txt = f"{r_peer.value * 100:.2f}%"
    else:
        bpm_value_txt = "—"
    surplus = snap[snap["entity_lei"] == data.BPM]
    if not surplus.empty and pd.notna(surplus["mrel_surplus_trea_pp"].iloc[0]):
        surplus_pp = surplus["mrel_surplus_trea_pp"].iloc[0]
        surplus_txt = f"{surplus_pp * 100:+.2f} pp vs requirement"
    else:
        surplus_txt = "no surplus data"

    badges = [
        _format_badge("BPM MREL % TREA", bpm_value_txt, surplus_txt, tone="red"),
        _format_badge(
            "Rank in peer set",
            f"{r_peer.rank} / {r_peer.total_with_data}"
            if r_peer.rank > 0 else "—",
            f"{r_peer.percentile:.0f}ᵗʰ percentile"
            if r_peer.rank > 0 else "no peer data",
        ),
        _format_badge(
            "Rank in EU universe",
            f"{r_univ.rank} / {r_univ.total_with_data}"
            if r_univ.rank > 0 else "—",
            f"{r_univ.percentile:.0f}ᵗʰ percentile across 113 banks"
            if r_univ.rank > 0 else "no universe data",
        ),
        _format_badge(
            "Peer median",
            f"{stats['median'] * 100:.2f}%"
            if pd.notna(stats.get("median")) else "—",
            f"n = {stats['n']} banks with data", tone="peer",
        ),
    ]

    trea_fig = _cushion_figure(wide, peer_leis, ref_date,
                               "mrel_pct_trea", "mrel_requirement_trea")
    tem_fig = _cushion_figure(wide, peer_leis, ref_date,
                              "mrel_pct_tem", "mrel_requirement_tem")
    return badges, trea_fig, tem_fig
