"""Maturity page (Q3) — residual-maturity heatmap per bank."""
from __future__ import annotations

import dash
import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, State, callback, dcc, html

from app import data
from app.components.export_button import export_bar, graph_config
from app.theme import BPM_COLOR, GREY_400, GREY_600, NAVY, apply_layout
from core.captions import MATURITY_BUCKET_LABELS, MATURITY_BUCKET_SOURCES
from core.metrics import TLAC3_MATURITY_BUCKETS, tlac3_maturity

dash.register_page(__name__, path="/maturity", name="Maturity", order=3)


BUCKET_KEYS = list(TLAC3_MATURITY_BUCKETS)
BUCKET_SHARE_COLS = [f"{k}_share" for k in BUCKET_KEYS]
BUCKET_LABELS = [MATURITY_BUCKET_LABELS[k] for k in BUCKET_KEYS]


def layout():
    return html.Div(
        [
            html.Div(
                [
                    html.H2("Maturity — residual-maturity profile"),
                    html.Div(
                        "Heatmap of each bank's MREL-eligible stack by residual "
                        "maturity bucket. Default sort lifts short-dated banks "
                        "(largest 1–2y share) to the top — a proxy for refi-wall "
                        "risk. BPM row is highlighted.",
                        className="caption",
                    ),
                ],
                className="page-header",
            ),
            html.Div(
                [
                    html.H3("Maturity shares"),
                    html.Div(
                        [
                            html.Span("Sort by: ",
                                      style={"fontSize": "12px",
                                             "color": GREY_600,
                                             "marginRight": "8px"}),
                            dcc.Dropdown(
                                id="maturity-sort",
                                options=[
                                    {"label": f"{MATURITY_BUCKET_LABELS[k]} share",
                                     "value": f"{k}_share"}
                                    for k in BUCKET_KEYS
                                ] + [
                                    {"label": "Total eligible (€)",
                                     "value": "total_eligible"},
                                    {"label": "Bank name (A→Z)",
                                     "value": "name"},
                                ],
                                value="maturity_1_to_2y_share",
                                clearable=False,
                                style={"width": "260px",
                                       "display": "inline-block"},
                            ),
                        ],
                        style={"display": "flex", "alignItems": "center",
                               "marginBottom": "10px"},
                    ),
                    html.Div(
                        [
                            html.Span("Colour scale: % of MREL-eligible stack."
                                      " Darker = larger share. ",
                                      style={"color": GREY_600}),
                            html.Br(),
                            html.Span(
                                "Source: K_97.00 rows 0060–0100, col c0050 "
                                "(Sum of 1 to n, i.e. aggregated across every "
                                "insolvency rank). Shares sum to 1.0 by "
                                "definition — MREL-eligible liabilities must "
                                "have residual maturity ≥ 1y.",
                                style={"color": GREY_600}),
                        ],
                        className="meta-line",
                    ),
                    export_bar("maturity"),
                    dcc.Graph(id="maturity-chart",
                              config=graph_config("mrel_maturity")),
                ],
                className="card",
            ),
            html.Div(
                [
                    html.H3("Bucket sources"),
                    html.Ul([
                        html.Li(
                            [
                                html.Span(MATURITY_BUCKET_LABELS[k],
                                          style={"fontWeight": 600,
                                                 "color": NAVY}),
                                html.Span(f"  ·  {MATURITY_BUCKET_SOURCES[k]}",
                                          style={"color": GREY_600,
                                                 "fontSize": "12px"}),
                            ],
                            style={"marginBottom": "4px"},
                        )
                        for k in BUCKET_KEYS
                    ]),
                ],
                className="card",
            ),
        ]
    )


@callback(
    Output("maturity-chart", "figure"),
    Input("peer-set", "value"),
    Input("reference-date", "value"),
    Input("maturity-sort", "value"),
)
def _render(peer_key, ref_date_iso, sort_key):
    fig = go.Figure()
    apply_layout(fig)

    mat = tlac3_maturity(data.load_facts())
    mat = mat.merge(
        data.load_banks()[["entity_lei", "entity_name"]],
        on="entity_lei", how="left",
    )
    if mat.empty or not peer_key or not ref_date_iso:
        fig.update_layout(height=400)
        fig.add_annotation(text="No maturity data",
                           showarrow=False, font={"color": GREY_400})
        return fig

    ref_date = pd.Timestamp(ref_date_iso)
    peer_leis = data.resolve_peers(peer_key)
    snap = mat[
        (mat["reference_date"] == ref_date)
        & (mat["entity_lei"].isin(peer_leis))
    ].dropna(subset=["total_eligible"]).copy()

    if snap.empty:
        fig.update_layout(height=400)
        fig.add_annotation(
            text="No peer-set TLAC3 maturity data for this date. "
                 "Subsidiaries file ILAC only — PDF ingestion in Phase 5 "
                 "closes the gap.",
            showarrow=False, font={"color": GREY_400},
        )
        return fig

    if sort_key == "name":
        snap = snap.sort_values("entity_name", ascending=False)
    else:
        snap = snap.sort_values(sort_key, ascending=True)

    labels = snap["entity_name"].fillna(snap["entity_lei"]).to_list()
    matrix = snap[BUCKET_SHARE_COLS].fillna(0).to_numpy()

    # Build hover text with both % and €bn per cell.
    hover = []
    for _, row in snap.iterrows():
        per_bank = []
        for k in BUCKET_KEYS:
            share = row.get(f"{k}_share") or 0
            amount = row.get(k) or 0
            per_bank.append(
                f"{row['entity_name'] or row['entity_lei']}<br>"
                f"{MATURITY_BUCKET_LABELS[k]}: {share * 100:.1f}% "
                f"(€{amount / 1e9:.2f}bn)"
            )
        hover.append(per_bank)

    fig.add_trace(go.Heatmap(
        z=matrix,
        x=BUCKET_LABELS,
        y=labels,
        colorscale=[
            [0.0, "#eef3f7"], [0.15, "#b9c7d7"], [0.35, "#7e96b1"],
            [0.6, "#3f5a7a"], [0.85, "#1c2f4a"], [1.0, "#0b2545"],
        ],
        zmin=0, zmax=1,
        colorbar={"tickformat": ".0%", "title": {"text": "Share"}},
        hovertext=hover, hoverinfo="text",
    ))

    # BPM row marker — a small red dot to the right of BPM's row.
    if data.BPM in snap["entity_lei"].to_list():
        bpm_name = snap.loc[snap["entity_lei"] == data.BPM, "entity_name"].iloc[0]
        fig.add_trace(go.Scatter(
            x=[BUCKET_LABELS[-1]],
            y=[bpm_name or data.BPM],
            mode="markers+text",
            marker={"size": 12, "color": BPM_COLOR, "symbol": "diamond"},
            text=["BPM"],
            textposition="middle right",
            textfont={"color": BPM_COLOR, "size": 11},
            hoverinfo="skip",
            showlegend=False,
        ))

    fig.update_layout(
        height=max(420, 28 * len(labels) + 140),
        margin={"l": 240, "r": 60, "t": 24, "b": 40},
        xaxis={"title": "Residual maturity bucket", "side": "top"},
        yaxis={"automargin": True,
               "tickfont": {"color": NAVY}},
        showlegend=False,
    )
    return fig


@callback(
    Output("maturity-export-csv-dl", "data"),
    Input("maturity-export-csv-btn", "n_clicks"),
    State("peer-set", "value"),
    State("reference-date", "value"),
    prevent_initial_call=True,
)
def _export_csv(n_clicks, peer_key, ref_date_iso):
    if not n_clicks or not peer_key or not ref_date_iso:
        return dash.no_update
    mat = tlac3_maturity(data.load_facts()).merge(
        data.load_banks()[["entity_lei", "entity_name", "country"]],
        on="entity_lei", how="left",
    )
    ref_date = pd.Timestamp(ref_date_iso)
    peer_leis = data.resolve_peers(peer_key)
    snap = mat[
        (mat["reference_date"] == ref_date)
        & (mat["entity_lei"].isin(peer_leis))
    ].copy()
    cols = (
        ["entity_lei", "entity_name", "country", "reference_date"]
        + BUCKET_KEYS + BUCKET_SHARE_COLS + ["total_eligible"]
    )
    snap = snap[[c for c in cols if c in snap.columns]]
    return dcc.send_data_frame(
        snap.to_csv, "mrel_maturity.csv", index=False,
    )
