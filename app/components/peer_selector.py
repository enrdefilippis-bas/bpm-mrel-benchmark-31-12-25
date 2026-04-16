"""Shared sidebar controls: peer-set, reference-date, normalisation toggle."""
from __future__ import annotations

from dash import dcc, html

from app import data


def peer_set_dropdown(selected_key: str | None = None) -> dcc.Dropdown:
    options = data.peer_set_options()
    default = selected_key or (options[0]["value"] if options else None)
    return dcc.Dropdown(
        id="peer-set",
        options=options,
        value=default,
        clearable=False,
        className="dcc-dropdown",
        style={"color": "#0b2545"},
    )


def reference_date_dropdown(selected_value: str | None = None) -> dcc.Dropdown:
    options = data.reference_date_options()
    default = selected_value or (options[0]["value"] if options else None)
    return dcc.Dropdown(
        id="reference-date",
        options=options,
        value=default,
        clearable=False,
        className="dcc-dropdown",
        style={"color": "#0b2545"},
    )


def normalisation_toggle() -> dcc.RadioItems:
    return dcc.RadioItems(
        id="normalisation",
        options=[
            {"label": " Percent", "value": "pct"},
            {"label": " €bn", "value": "eur"},
        ],
        value="pct",
        inline=True,
        inputStyle={"marginRight": "4px"},
        labelStyle={"color": "#e6ecf2", "marginRight": "12px", "fontSize": "12px"},
    )


def sidebar_controls() -> html.Div:
    """The shared block of controls rendered in every page's sidebar."""
    return html.Div(
        [
            html.Div("Filters", className="section-title"),
            html.Div("Peer set", className="control-label"),
            peer_set_dropdown(),
            html.Div("Reference date", className="control-label"),
            reference_date_dropdown(),
            html.Div("Units", className="control-label"),
            normalisation_toggle(),
        ]
    )
