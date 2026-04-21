"""Cushion page (Q1) — MREL capacity vs requirement across peer set.

On the TREA basis we show **two** side-by-side charts to keep the CBR
treatment visible:

- **Cushion vs MREL (ex-CBR)** — capacity vs the requirement on a
  comparable ex-CBR base. This is the metric for peer-to-peer
  comparability because a handful of banks disclose their requirement
  including CBR (Iccrea, Mediobanca, BBVA) and others disclose it
  excluding CBR (the KM2 filing convention). ``core.cbr`` normalizes
  both into an ex-CBR base.

- **Cushion vs OCR (with-CBR)** — capacity vs requirement + CBR. This is
  the M-MDA threshold: if it goes negative, dividend / coupon / bonus
  restrictions trigger.

A TEM card sits below — TEM is not affected by the CBR treatment so a
single chart is enough.

BPM is highlighted; peers ordered by capacity.
"""
from __future__ import annotations

import dash
import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, State, callback, dcc, html

from app import data
from app.components.export_button import export_bar, graph_config
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
                        "Each bar shows a bank's MREL capacity; the amber "
                        "marker is the binding requirement. The two TREA "
                        "charts differ only in how the CBR is treated: the "
                        "left chart uses the MREL requirement on a comparable "
                        "ex-CBR base (peer-comparable), the right chart adds "
                        "CBR to get the OCR threshold (below which M-MDA "
                        "restrictions trigger). BPM is highlighted in red.",
                        className="caption",
                    ),
                ],
                className="page-header",
            ),
            html.Div(id="cushion-badges",
                     style={"display": "flex", "gap": "12px",
                            "marginBottom": "16px", "flexWrap": "wrap"}),
            export_bar("cushion"),
            html.Div(
                [
                    html.H3("MREL as % of TREA"),
                    html.Div(
                        "Two views side-by-side — same capacity bars, "
                        "different requirement marker.",
                        className="caption",
                    ),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.H4(
                                        "Cushion vs MREL (ex-CBR)",
                                        style={"marginBottom": "4px"},
                                    ),
                                    metric_methodology(
                                        "mrel_surplus_trea_ex_cbr_pp"
                                    ),
                                    dcc.Graph(
                                        id="cushion-trea-ex-cbr-chart",
                                        config=graph_config(
                                            "mrel_cushion_trea_ex_cbr"
                                        ),
                                        style={"height": "620px"},
                                    ),
                                ],
                                style={"flex": "1", "minWidth": "0"},
                            ),
                            html.Div(
                                [
                                    html.H4(
                                        "Cushion vs OCR (with-CBR)",
                                        style={"marginBottom": "4px"},
                                    ),
                                    metric_methodology(
                                        "mrel_surplus_trea_with_cbr_pp"
                                    ),
                                    dcc.Graph(
                                        id="cushion-trea-with-cbr-chart",
                                        config=graph_config(
                                            "mrel_cushion_trea_with_cbr"
                                        ),
                                        style={"height": "620px"},
                                    ),
                                ],
                                style={"flex": "1", "minWidth": "0"},
                            ),
                        ],
                        style={"display": "flex", "gap": "16px",
                               "flexWrap": "wrap"},
                    ),
                ],
                className="card",
            ),
            html.Div(
                [
                    html.H3("Subordination as % of TREA"),
                    html.Div(
                        "Same two-view structure as MREL: subordinated "
                        "capacity vs subordination requirement, ex-CBR and "
                        "with-CBR. Follows the same per-bank CBR treatment "
                        "as the total-MREL requirement.",
                        className="caption",
                    ),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.H4(
                                        "Subord cushion vs req (ex-CBR)",
                                        style={"marginBottom": "4px"},
                                    ),
                                    metric_methodology(
                                        "subord_surplus_trea_ex_cbr_pp"
                                    ),
                                    dcc.Graph(
                                        id="cushion-subord-trea-ex-cbr-chart",
                                        config=graph_config(
                                            "mrel_subord_cushion_trea_ex_cbr"
                                        ),
                                        style={"height": "620px"},
                                    ),
                                ],
                                style={"flex": "1", "minWidth": "0"},
                            ),
                            html.Div(
                                [
                                    html.H4(
                                        "Subord cushion vs req + CBR",
                                        style={"marginBottom": "4px"},
                                    ),
                                    metric_methodology(
                                        "subord_surplus_trea_with_cbr_pp"
                                    ),
                                    dcc.Graph(
                                        id="cushion-subord-trea-with-cbr-chart",
                                        config=graph_config(
                                            "mrel_subord_cushion_trea_with_cbr"
                                        ),
                                        style={"height": "620px"},
                                    ),
                                ],
                                style={"flex": "1", "minWidth": "0"},
                            ),
                        ],
                        style={"display": "flex", "gap": "16px",
                               "flexWrap": "wrap"},
                    ),
                ],
                className="card",
            ),
            html.Div(
                [
                    html.H3("MREL as % of TEM"),
                    metric_methodology("mrel_pct_tem"),
                    dcc.Graph(id="cushion-tem-chart",
                              config=graph_config("mrel_cushion_tem"),
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
        style={"flex": "1", "margin": "0", "minWidth": "200px"},
    )


def _cushion_figure(
    wide: pd.DataFrame,
    peer_leis: list[str],
    ref_date: pd.Timestamp,
    capacity_key: str,
    requirement_key: str,
    capacity_label: str | None = None,
    requirement_label: str = "Requirement",
) -> go.Figure:
    fig = go.Figure()
    apply_layout(fig)
    caption = get_caption(capacity_key)
    cap_label = capacity_label or caption.label

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
    if requirement_key in snap.columns:
        requirement = snap[requirement_key].to_list()
    else:
        requirement = [None] * len(snap)
    is_bpm = (snap["entity_lei"] == data.BPM).to_list()

    bar_colors = [BPM_COLOR if b else PEER_COLOR for b in is_bpm]
    capacity_hover = [
        f"{n}<br>Capacity: {c * 100:.2f}%"
        f"{('<br>' + requirement_label + ': ' + f'{r * 100:.2f}%') if r is not None and pd.notna(r) else ''}"
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
            name=requirement_label,
            hovertemplate=requirement_label + ": %{x:.2%}<extra></extra>",
        ))

    fig.update_layout(
        xaxis={"tickformat": ".0%", "title": cap_label},
        yaxis={"automargin": True},
        showlegend=True,
        legend={"orientation": "h", "y": 1.02, "x": 1, "xanchor": "right"},
        height=max(380, 22 * len(labels) + 140),
        margin={"l": 220, "r": 24, "t": 48, "b": 40},
    )
    return fig


@callback(
    Output("cushion-badges", "children"),
    Output("cushion-trea-ex-cbr-chart", "figure"),
    Output("cushion-trea-with-cbr-chart", "figure"),
    Output("cushion-subord-trea-ex-cbr-chart", "figure"),
    Output("cushion-subord-trea-with-cbr-chart", "figure"),
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
            empty_fig, empty_fig, empty_fig, empty_fig, empty_fig,
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

    # Pull BPM's two surplus views from the CBR-aware columns.
    bpm_row = snap[snap["entity_lei"] == data.BPM]
    def _surplus_txt(col: str, suffix: str) -> str:
        if bpm_row.empty or col not in bpm_row.columns:
            return "no data"
        v = bpm_row[col].iloc[0]
        if pd.isna(v):
            return "no data"
        return f"{v * 100:+.2f} pp vs {suffix}"

    surplus_txt_legacy = _surplus_txt("mrel_surplus_trea_pp", "requirement")
    surplus_ex_cbr_txt = _surplus_txt("mrel_surplus_trea_ex_cbr_pp", "MREL (ex-CBR)")
    surplus_with_cbr_txt = _surplus_txt("mrel_surplus_trea_with_cbr_pp", "OCR (with-CBR)")

    # CBR caveat for the BPM tile (if an estimate was used).
    cbr_note = ""
    if not bpm_row.empty and "cbr_is_estimate" in bpm_row.columns:
        is_est = bool(bpm_row["cbr_is_estimate"].iloc[0])
        treatment = str(bpm_row["cbr_treatment"].iloc[0]) if "cbr_treatment" in bpm_row.columns else ""
        cbr_note = (
            f"CBR: {treatment}" + (" (estimated)" if is_est else "")
        )

    badges = [
        _format_badge("BPM MREL % TREA", bpm_value_txt,
                      surplus_txt_legacy, tone="red"),
        _format_badge("BPM cushion vs MREL (ex-CBR)",
                      surplus_ex_cbr_txt,
                      cbr_note, tone="red"),
        _format_badge("BPM cushion vs OCR (with-CBR)",
                      surplus_with_cbr_txt,
                      "M-MDA breach if < 0", tone="red"),
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

    trea_ex_cbr_fig = _cushion_figure(
        wide, peer_leis, ref_date,
        capacity_key="mrel_pct_trea",
        requirement_key="mrel_requirement_trea_ex_cbr",
        capacity_label="MREL % TREA — requirement on ex-CBR base",
        requirement_label="Requirement (ex-CBR)",
    )
    trea_with_cbr_fig = _cushion_figure(
        wide, peer_leis, ref_date,
        capacity_key="mrel_pct_trea",
        requirement_key="mrel_requirement_trea_with_cbr",
        capacity_label="MREL % TREA — requirement + CBR (OCR threshold)",
        requirement_label="OCR (MREL + CBR)",
    )
    subord_ex_cbr_fig = _cushion_figure(
        wide, peer_leis, ref_date,
        capacity_key="subord_pct_trea",
        requirement_key="mrel_subord_requirement_trea_ex_cbr",
        capacity_label="Subord % TREA — requirement on ex-CBR base",
        requirement_label="Subord requirement (ex-CBR)",
    )
    subord_with_cbr_fig = _cushion_figure(
        wide, peer_leis, ref_date,
        capacity_key="subord_pct_trea",
        requirement_key="mrel_subord_requirement_trea_with_cbr",
        capacity_label="Subord % TREA — requirement + CBR",
        requirement_label="Subord requirement + CBR",
    )
    tem_fig = _cushion_figure(
        wide, peer_leis, ref_date,
        capacity_key="mrel_pct_tem",
        requirement_key="mrel_requirement_tem",
    )
    return (
        badges,
        trea_ex_cbr_fig, trea_with_cbr_fig,
        subord_ex_cbr_fig, subord_with_cbr_fig,
        tem_fig,
    )


@callback(
    Output("cushion-export-csv-dl", "data"),
    Input("cushion-export-csv-btn", "n_clicks"),
    State("peer-set", "value"),
    State("reference-date", "value"),
    prevent_initial_call=True,
)
def _export_csv(n_clicks, peer_key, ref_date_iso):
    if not n_clicks or not peer_key or not ref_date_iso:
        return dash.no_update
    wide = data.load_km2()
    ref_date = pd.Timestamp(ref_date_iso)
    peer_leis = data.resolve_peers(peer_key)
    base_cols = [
        "entity_lei", "entity_name", "country", "reference_date",
        "mrel_pct_trea", "mrel_requirement_trea", "mrel_surplus_trea_pp",
        "cbr_pct_trea", "cbr_treatment", "cbr_is_estimate", "cbr_source",
        "mrel_requirement_trea_ex_cbr", "mrel_requirement_trea_with_cbr",
        "mrel_surplus_trea_ex_cbr_pp", "mrel_surplus_trea_with_cbr_pp",
        "subord_pct_trea", "mrel_subord_requirement_trea",
        "mrel_subord_requirement_trea_ex_cbr",
        "mrel_subord_requirement_trea_with_cbr",
        "subord_surplus_trea_ex_cbr_pp", "subord_surplus_trea_with_cbr_pp",
        "mrel_pct_tem", "mrel_requirement_tem", "mrel_surplus_tem_pp",
        "subordination_ratio",
    ]
    # Only include columns that exist (defensive against older ingests).
    cols = [c for c in base_cols if c in wide.columns]
    snap = wide[
        (wide["reference_date"] == ref_date)
        & (wide["entity_lei"].isin(peer_leis))
    ][cols].sort_values("mrel_pct_trea", ascending=False)
    return dcc.send_data_frame(snap.to_csv, "mrel_cushion.csv", index=False)
