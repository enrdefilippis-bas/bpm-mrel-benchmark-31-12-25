"""Per-page export toolbar — CSV download + PNG-download config for Plotly.

Every drill-down page embeds :func:`export_bar` once and one callback that
fills the matching ``dcc.Download`` with :func:`dash.dcc.send_data_frame`.
Every :class:`dash.dcc.Graph` that wants a PNG-export button in its
modebar uses :func:`graph_config` so the filename, resolution and
removed buttons are consistent across the app.
"""
from __future__ import annotations

from dash import dcc, html


def export_bar(page_id: str, *, csv_label: str = "Download CSV") -> html.Div:
    """Render the export toolbar for a page.

    ``page_id`` is used to namespace the button and Download component
    ids: ``{page_id}-export-csv-btn`` and ``{page_id}-export-csv-dl``.
    """
    return html.Div(
        [
            html.Button(
                csv_label,
                id=f"{page_id}-export-csv-btn",
                n_clicks=0,
                className="export-btn",
            ),
            html.Span(
                "  · PNG: chart modebar → camera icon",
                className="export-hint",
            ),
            dcc.Download(id=f"{page_id}-export-csv-dl"),
        ],
        className="export-bar",
    )


def graph_config(filename: str, *, height: int = 720,
                 width: int = 1280) -> dict:
    """Plotly ``dcc.Graph`` config that exposes a clean PNG-export modebar."""
    return {
        "displayModeBar": True,
        "displaylogo": False,
        "modeBarButtonsToRemove": [
            "zoom2d", "pan2d", "select2d", "lasso2d",
            "autoScale2d", "zoomIn2d", "zoomOut2d",
            "hoverClosestCartesian", "hoverCompareCartesian",
        ],
        "toImageButtonOptions": {
            "format": "png",
            "filename": filename,
            "height": height,
            "width": width,
            "scale": 2,
        },
    }
