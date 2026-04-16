"""Country page (Q7) — per-country distribution of MREL/capacity metrics.

Box plot per country for a chosen KM2 metric. Individual bank dots shown
on top so countries with only one or two banks still register visibly.
Italy highlighted (BPM's home) and BPM drawn as a red diamond.
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
    STEEL,
    apply_layout,
)
from core.captions import get_caption

dash.register_page(__name__, path="/country", name="Country", order=6)


METRIC_OPTIONS = [
    {"label": "MREL % TREA", "value": "mrel_pct_trea"},
    {"label": "MREL % TEM", "value": "mrel_pct_tem"},
    {"label": "Subord % TREA", "value": "subord_pct_trea"},
    {"label": "Surplus TREA (pp)", "value": "mrel_surplus_trea_pp"},
    {"label": "Subordination ratio", "value": "subordination_ratio"},
    {"label": "MREL requirement % TREA", "value": "mrel_requirement_trea"},
]

ITALY = "Italy"


def layout():
    return html.Div(
        [
            html.Div(
                [
                    html.H2("Country — distribution by jurisdiction"),
                    html.Div(
                        "Box plot per country for the chosen metric: median, "
                        "IQR, whiskers, individual banks overlaid as dots. "
                        "Italy is highlighted; BPM is the red diamond. "
                        "Countries with a single bank reporting (e.g. Italy "
                        "in the raw EBA export) show just that point until "
                        "Phase 5 adds Intesa and UniCredit.",
                        className="caption",
                    ),
                ],
                className="page-header",
            ),
            html.Div(
                [
                    html.H3("Distribution by country"),
                    html.Div(
                        [
                            html.Span("Metric: ",
                                      style={"fontSize": "12px",
                                             "color": GREY_600,
                                             "marginRight": "8px"}),
                            dcc.Dropdown(
                                id="country-metric",
                                options=METRIC_OPTIONS,
                                value="mrel_pct_trea",
                                clearable=False,
                                style={"width": "260px",
                                       "display": "inline-block"},
                            ),
                            html.Span("Sort countries by: ",
                                      style={"fontSize": "12px",
                                             "color": GREY_600,
                                             "marginLeft": "20px",
                                             "marginRight": "8px"}),
                            dcc.Dropdown(
                                id="country-sort",
                                options=[
                                    {"label": "Median (high → low)",
                                     "value": "median_desc"},
                                    {"label": "Median (low → high)",
                                     "value": "median_asc"},
                                    {"label": "Bank count (high → low)",
                                     "value": "count_desc"},
                                    {"label": "Country name (A → Z)",
                                     "value": "name"},
                                ],
                                value="median_desc",
                                clearable=False,
                                style={"width": "220px",
                                       "display": "inline-block"},
                            ),
                        ],
                        style={"display": "flex", "alignItems": "center",
                               "flexWrap": "wrap",
                               "rowGap": "8px",
                               "marginBottom": "10px"},
                    ),
                    html.Div(id="country-methodology", className="meta-line"),
                    dcc.Graph(id="country-chart",
                              config={"displayModeBar": False}),
                ],
                className="card",
            ),
            html.Div(
                [
                    html.H3("Coverage"),
                    html.Div(id="country-coverage",
                             style={"color": GREY_600, "fontSize": "13px"}),
                ],
                className="card",
            ),
        ]
    )


def _format_hover(unit: str, names, values, country):
    if unit == "%":
        return [f"{n}<br>{country}: {v * 100:.2f}%"
                for n, v in zip(names, values)]
    if unit == "pp":
        return [f"{n}<br>{country}: {v * 100:+.2f} pp"
                for n, v in zip(names, values)]
    if unit == "€bn":
        return [f"{n}<br>{country}: €{v / 1e9:.2f}bn"
                for n, v in zip(names, values)]
    return [f"{n}<br>{country}: {v:.3f}"
            for n, v in zip(names, values)]


@callback(
    Output("country-chart", "figure"),
    Output("country-methodology", "children"),
    Output("country-coverage", "children"),
    Input("country-metric", "value"),
    Input("country-sort", "value"),
    Input("reference-date", "value"),
)
def _render(metric_key, sort_key, ref_date_iso):
    fig = go.Figure()
    apply_layout(fig)
    caption = get_caption(metric_key)

    wide = data.load_km2()
    if wide.empty or not ref_date_iso:
        fig.update_layout(height=400)
        fig.add_annotation(text="No data",
                           showarrow=False, font={"color": GREY_400})
        return fig, metric_methodology(metric_key), "—"

    ref_date = pd.Timestamp(ref_date_iso)
    snap = wide[wide["reference_date"] == ref_date].dropna(
        subset=[metric_key, "country"]
    ).copy()

    if snap.empty:
        fig.update_layout(height=400)
        fig.add_annotation(text=f"No {caption.short_label} data for "
                                f"{ref_date.date()}.",
                           showarrow=False, font={"color": GREY_400})
        return fig, metric_methodology(metric_key), "—"

    # Order countries.
    agg = (
        snap.groupby("country")[metric_key]
            .agg(["median", "count"])
            .reset_index()
    )
    if sort_key == "median_desc":
        agg = agg.sort_values("median", ascending=True)  # bottom-up on y-axis
    elif sort_key == "median_asc":
        agg = agg.sort_values("median", ascending=False)
    elif sort_key == "count_desc":
        agg = agg.sort_values("count", ascending=True)
    else:
        agg = agg.sort_values("country", ascending=False)

    country_order = agg["country"].to_list()

    # One trace per country so we can colour Italy distinctly.
    for country in country_order:
        rows = snap[snap["country"] == country]
        values = rows[metric_key].to_numpy()
        names = rows["entity_name"].fillna(rows["entity_lei"]).to_numpy()

        is_italy = country == ITALY
        fill = "rgba(192, 54, 44, 0.15)" if is_italy else "rgba(74, 106, 138, 0.12)"
        line = BPM_COLOR if is_italy else STEEL

        fig.add_trace(go.Box(
            x=values,
            y=[country] * len(values),
            orientation="h",
            name=country,
            boxpoints="all",
            pointpos=0,
            jitter=0.35,
            fillcolor=fill,
            line={"color": line, "width": 1.5},
            marker={"color": PEER_COLOR if not is_italy else BPM_COLOR,
                    "size": 6, "opacity": 0.85,
                    "line": {"width": 0.4, "color": NAVY}},
            hovertext=_format_hover(caption.unit, names, values, country),
            hoverinfo="text",
            showlegend=False,
        ))

    # BPM red diamond on top of Italy.
    bpm_row = snap[snap["entity_lei"] == data.BPM]
    if not bpm_row.empty:
        bpm_val = float(bpm_row[metric_key].iloc[0])
        bpm_country = bpm_row["country"].iloc[0]
        fig.add_trace(go.Scatter(
            x=[bpm_val], y=[bpm_country],
            mode="markers+text",
            marker={"size": 14, "color": BPM_COLOR, "symbol": "diamond",
                    "line": {"width": 1.5, "color": "white"}},
            text=["BPM"], textposition="middle right",
            textfont={"color": BPM_COLOR, "size": 11},
            hoverinfo="skip",
            showlegend=False,
        ))

    if caption.unit in ("%", "pp"):
        fig.update_xaxes(tickformat=".0%")
    elif caption.unit == "€bn":
        fig.update_xaxes(tickprefix="€", ticksuffix="bn", tickformat=".2s")

    fig.update_layout(
        height=max(420, 28 * len(country_order) + 160),
        margin={"l": 160, "r": 40, "t": 24, "b": 40},
        xaxis={"title": caption.label},
        yaxis={"automargin": True, "tickfont": {"color": NAVY}},
    )

    total_banks = int(agg["count"].sum())
    country_count = len(country_order)
    multi_bank = int((agg["count"] >= 3).sum())
    coverage = (
        f"{total_banks} banks across {country_count} countries at "
        f"{ref_date.date()}; {multi_bank} countries have ≥3 banks "
        "(meaningful box-plot IQR). Phase 5 adds Intesa, UniCredit, BBVA, "
        "Crédit Agricole, Société Générale — bolstering Italy / Spain / "
        "France coverage."
    )
    return fig, metric_methodology(metric_key), coverage
