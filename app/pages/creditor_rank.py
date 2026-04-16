"""Creditor ranking page (Q6) — TLAC3 / TLAC3b insolvency-rank stack.

Each bank's MREL-eligible liabilities broken down by insolvency rank.
Toggle between resolution entity (K_97.00 — TLAC3) and non-resolution
subsidiary (K_98.00 — TLAC3b) scopes.

Colour encodes seniority: low rank numbers (more senior) in steel, higher
rank numbers (more subordinated) in amber, to echo the composition page.
"""
from __future__ import annotations

import dash
import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, State, callback, dcc, html

from app import data
from app.components.export_button import export_bar, graph_config
from app.theme import BPM_COLOR, GREY_400, GREY_600, NAVY, apply_layout
from core.captions import CREDITOR_SCOPE_DESCRIPTION, CREDITOR_SCOPE_LABELS
from core.metrics import CREDITOR_RANK_SOURCES, creditor_rank_breakdown

dash.register_page(__name__, path="/creditor-rank", name="Creditor rank", order=5)


# Discrete palette over the master-scale rank numbers observed in the
# EBA export. Rank 1 = most senior; higher = more subordinated.
RANK_COLORS: dict[int, str] = {
    1:  "#7d96b0",  # senior — steel-light
    2:  "#627e9a",
    3:  "#4a6a8a",  # steel
    4:  "#3e5772",
    5:  "#d8a946",  # amber-mid
    6:  "#e6a817",  # amber
    7:  "#d69516",
    8:  "#c0362c",  # red — deeply subordinated
    9:  "#a82f26",
    10: "#8b271f",
}
DEFAULT_RANK_COLOR = "#7a7a7a"


def _rank_color(rank: int) -> str:
    return RANK_COLORS.get(rank, DEFAULT_RANK_COLOR)


def _sort_options():
    return [
        {"label": "Total eligible (€ desc)", "value": "total_desc"},
        {"label": "Senior share (Rank 1–2)", "value": "senior_share"},
        {"label": "Deep-subord share (Rank ≥ 5)", "value": "subord_share"},
        {"label": "Bank name (A → Z)", "value": "name"},
    ]


def layout():
    return html.Div(
        [
            html.Div(
                [
                    html.H2("Creditor ranking — MREL stack by insolvency rank"),
                    html.Div(
                        "Each bar shows one bank's MREL-eligible liabilities "
                        "(and own funds) split by insolvency-master-scale "
                        "rank. Lower rank numbers sit higher in the creditor "
                        "hierarchy — they are paid first in resolution. "
                        "Toggle the scope to switch between the resolution "
                        "entity and non-resolution subsidiaries.",
                        className="caption",
                    ),
                ],
                className="page-header",
            ),
            html.Div(
                [
                    html.H3("Rank composition"),
                    html.Div(
                        [
                            html.Span("Scope: ",
                                      style={"fontSize": "12px",
                                             "color": GREY_600,
                                             "marginRight": "8px"}),
                            dcc.RadioItems(
                                id="creditor-scope",
                                options=[
                                    {"label": f"  {CREDITOR_SCOPE_LABELS[k]}",
                                     "value": k}
                                    for k in CREDITOR_RANK_SOURCES
                                ],
                                value="resolution",
                                inline=True,
                                labelStyle={"marginRight": "18px",
                                            "fontSize": "13px"},
                                inputStyle={"marginRight": "4px"},
                            ),
                            html.Span("View: ",
                                      style={"fontSize": "12px",
                                             "color": GREY_600,
                                             "marginLeft": "20px",
                                             "marginRight": "8px"}),
                            dcc.RadioItems(
                                id="creditor-mode",
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
                                             "marginLeft": "20px",
                                             "marginRight": "8px"}),
                            dcc.Dropdown(
                                id="creditor-sort",
                                options=_sort_options(),
                                value="total_desc",
                                clearable=False,
                                style={"width": "260px",
                                       "display": "inline-block"},
                            ),
                        ],
                        style={"display": "flex", "alignItems": "center",
                               "flexWrap": "wrap",
                               "rowGap": "8px",
                               "marginBottom": "10px"},
                    ),
                    html.Div(id="creditor-methodology", className="meta-line"),
                    export_bar("creditor"),
                    dcc.Graph(id="creditor-chart",
                              config=graph_config("mrel_creditor_rank")),
                ],
                className="card",
            ),
            html.Div(
                [
                    html.H3("How to read this"),
                    html.Div(
                        [
                            html.P(
                                "The 'Ranking in insolvency (master scale)' "
                                "field in the EBA template maps each liability "
                                "to a numeric rank. A rank of 1 is the most "
                                "senior (creditors paid first), the highest "
                                "observed rank is the most junior. Segments "
                                "coloured steel = senior; amber/red = deeply "
                                "subordinated.",
                                style={"color": GREY_600, "fontSize": "13px",
                                       "marginBottom": "8px"},
                            ),
                            html.P(
                                "Banks that file ILAC only (subsidiaries of "
                                "non-EU G-SIIs, e.g. US-based parents) have "
                                "no TLAC3 row and simply do not appear here.",
                                style={"color": GREY_600, "fontSize": "13px",
                                       "marginBottom": "0"},
                            ),
                        ],
                    ),
                ],
                className="card",
            ),
        ]
    )


def _methodology(scope: str) -> str:
    tpl, row, col = CREDITOR_RANK_SOURCES[scope]
    return (
        f"Source: EBA Pillar 3 template {tpl}, row {row} col c{col} filtered "
        f"by Open Key 'Ranking in insolvency = Rank N'. "
        f"{CREDITOR_SCOPE_DESCRIPTION[scope]}"
    )


def _share(pivot: pd.DataFrame, rank_cols: list[int],
           ranks_present: list[int]) -> pd.Series:
    """Share of ``rank_cols`` within the total across all ``ranks_present``."""
    total = pivot[ranks_present].sum(axis=1).replace(0, pd.NA)
    if not rank_cols:
        return pd.Series(0.0, index=pivot.index)
    return pivot[rank_cols].sum(axis=1) / total


@callback(
    Output("creditor-chart", "figure"),
    Output("creditor-methodology", "children"),
    Input("peer-set", "value"),
    Input("reference-date", "value"),
    Input("creditor-scope", "value"),
    Input("creditor-mode", "value"),
    Input("creditor-sort", "value"),
)
def _render(peer_key, ref_date_iso, scope, mode, sort_key):
    fig = go.Figure()
    apply_layout(fig)

    if not peer_key or not ref_date_iso:
        fig.update_layout(height=400)
        fig.add_annotation(text="No data", showarrow=False,
                           font={"color": GREY_400})
        return fig, _methodology(scope)

    ref_date = pd.Timestamp(ref_date_iso)
    peer_leis = data.resolve_peers(peer_key)

    br = creditor_rank_breakdown(data.load_facts(), scope=scope)
    br = br[(br["reference_date"] == ref_date)
            & (br["entity_lei"].isin(peer_leis))]

    if br.empty:
        fig.update_layout(height=400)
        fig.add_annotation(
            text=f"No {scope.replace('_', ' ')}-scope data for this peer set "
                 f"on {ref_date.date()}.",
            showarrow=False, font={"color": GREY_400},
        )
        return fig, _methodology(scope)

    # Drop zero-amount segments to keep bars tidy.
    br = br[br["value"].fillna(0) > 0]
    if br.empty:
        fig.update_layout(height=400)
        fig.add_annotation(
            text=f"All reported amounts are zero for this peer set "
                 f"on {ref_date.date()}.",
            showarrow=False, font={"color": GREY_400},
        )
        return fig, _methodology(scope)

    pivot = (
        br.pivot_table(index="entity_lei", columns="rank",
                       values="value", aggfunc="sum")
          .fillna(0)
    )
    pivot.columns = [int(c) for c in pivot.columns]
    ranks_present = sorted(pivot.columns)

    names = data.load_banks().set_index("entity_lei")["entity_name"].to_dict()
    pivot["entity_name"] = [names.get(lei, lei) for lei in pivot.index]
    pivot["total"] = pivot[ranks_present].sum(axis=1)
    pivot["senior_share"] = _share(
        pivot, [r for r in ranks_present if r <= 2], ranks_present,
    )
    pivot["subord_share"] = _share(
        pivot, [r for r in ranks_present if r >= 5], ranks_present,
    )

    if sort_key == "name":
        pivot = pivot.sort_values("entity_name", ascending=False)
    elif sort_key == "total_desc":
        pivot = pivot.sort_values("total", ascending=True)
    elif sort_key == "senior_share":
        pivot = pivot.sort_values("senior_share", ascending=True)
    elif sort_key == "subord_share":
        pivot = pivot.sort_values("subord_share", ascending=True)

    labels = pivot["entity_name"].to_list()
    totals = pivot["total"].to_list()

    for rank in ranks_present:
        vals = pivot[rank].to_list()
        if mode == "pct":
            xs = [v / t if t else 0 for v, t in zip(vals, totals)]
            hover = [
                f"{n}<br>Rank {rank}: "
                f"{(v / t * 100 if t else 0):.1f}% (€{v / 1e9:.2f}bn)"
                for n, v, t in zip(labels, vals, totals)
            ]
        else:
            xs = [v / 1e9 for v in vals]
            hover = [
                f"{n}<br>Rank {rank}: €{v / 1e9:.2f}bn"
                f" ({(v / t * 100 if t else 0):.1f}%)"
                for n, v, t in zip(labels, vals, totals)
            ]
        fig.add_trace(go.Bar(
            y=labels, x=xs, orientation="h",
            name=f"Rank {rank}",
            marker={"color": _rank_color(rank)},
            hovertext=hover, hoverinfo="text",
        ))

    # BPM annotation — small red diamond at end of BPM's bar.
    if data.BPM in pivot.index:
        bpm_name = pivot.loc[data.BPM, "entity_name"]
        bpm_total = pivot.loc[data.BPM, "total"]
        x_marker = 1.0 if mode == "pct" else bpm_total / 1e9
        fig.add_trace(go.Scatter(
            x=[x_marker], y=[bpm_name],
            mode="markers+text",
            marker={"size": 12, "color": BPM_COLOR, "symbol": "diamond",
                    "line": {"width": 1.5, "color": "white"}},
            text=["BPM"], textposition="middle right",
            textfont={"color": BPM_COLOR, "size": 11},
            hoverinfo="skip",
            showlegend=False,
        ))

    if mode == "pct":
        x_title = "Share of MREL-eligible stack"
        x_format = ".0%"
        x_range = [0, 1.08]
    else:
        x_title = "MREL-eligible stack (€bn)"
        x_format = ".1f"
        x_range = None

    fig.update_layout(
        barmode="stack",
        height=max(380, 26 * len(labels) + 160),
        margin={"l": 240, "r": 80, "t": 24, "b": 40},
        xaxis={"title": x_title, "tickformat": x_format, "range": x_range},
        yaxis={"automargin": True, "tickfont": {"color": NAVY}},
        legend={"orientation": "h", "y": 1.04, "x": 1,
                "xanchor": "right", "title": {"text": "Insolvency rank"}},
    )
    return fig, _methodology(scope)


@callback(
    Output("creditor-export-csv-dl", "data"),
    Input("creditor-export-csv-btn", "n_clicks"),
    State("peer-set", "value"),
    State("reference-date", "value"),
    State("creditor-scope", "value"),
    prevent_initial_call=True,
)
def _export_csv(n_clicks, peer_key, ref_date_iso, scope):
    if not n_clicks or not peer_key or not ref_date_iso:
        return dash.no_update
    ref_date = pd.Timestamp(ref_date_iso)
    peer_leis = data.resolve_peers(peer_key)
    br = creditor_rank_breakdown(data.load_facts(), scope=scope)
    br = br[(br["reference_date"] == ref_date)
            & (br["entity_lei"].isin(peer_leis))].copy()
    names = data.load_banks().set_index("entity_lei")["entity_name"].to_dict()
    br["entity_name"] = br["entity_lei"].map(names)
    br["scope"] = scope
    snap = br[["entity_lei", "entity_name", "scope", "reference_date",
               "rank", "value"]].sort_values(["entity_name", "rank"])
    return dcc.send_data_frame(
        snap.to_csv, f"mrel_creditor_rank_{scope}.csv", index=False,
    )
