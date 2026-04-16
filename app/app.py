"""Dash entry point.

Wires the sidebar shell, the shared filter controls, the page router, and
injects the global CSS. Run:

    python -m app.app

and open http://localhost:8050.
"""
from __future__ import annotations

import dash
from dash import dcc, html

from app import data
from app.components.peer_selector import sidebar_controls
from app.theme import GLOBAL_CSS


def _build_app() -> dash.Dash:
    app = dash.Dash(
        __name__,
        use_pages=True,
        pages_folder="pages",
        title="MREL Peer Benchmark",
        suppress_callback_exceptions=True,
    )
    app.index_string = f"""<!DOCTYPE html>
<html>
<head>
    {{%metas%}}
    <title>{{%title%}}</title>
    {{%favicon%}}
    {{%css%}}
    {GLOBAL_CSS}
</head>
<body>
    {{%app_entry%}}
    <footer>
        {{%config%}}
        {{%scripts%}}
        {{%renderer%}}
    </footer>
</body>
</html>"""
    app.layout = _layout
    return app


def _nav_links() -> list:
    """Sidebar nav links for every registered page, in declared order."""
    pages = sorted(
        dash.page_registry.values(),
        key=lambda p: p.get("order", 99),
    )
    return [
        dcc.Link(p["name"], href=p["relative_path"], className="nav-link",
                 id=f"nav-{p['relative_path']}")
        for p in pages
    ]


def _header_meta() -> html.Div:
    """Data-presence banner + context (n banks, ref dates available)."""
    if not data.data_is_loaded():
        return html.Div(
            "Data not yet ingested — run scripts/ingest.py first.",
            style={"color": "#f3c96a", "fontSize": "12px", "marginBottom": "8px"},
        )
    banks = data.load_banks()
    dates = data.available_reference_dates()
    latest = dates[-1] if dates else None
    txt = f"{len(banks)} banks · {len(dates)} reference dates"
    if latest is not None:
        import pandas as pd
        txt += f" · latest {pd.Timestamp(latest).date()}"
    return html.Div(
        txt,
        style={"color": "#9aa4b1", "fontSize": "11px", "marginBottom": "8px"},
    )


def _layout():
    sidebar = html.Div(
        [
            html.H1("MREL Benchmark"),
            html.Div("BPM vs peer banks · EBA Pillar 3",
                     className="subtitle"),
            _header_meta(),
            html.Div("Pages", className="section-title"),
            html.Div(_nav_links()),
            sidebar_controls(),
        ],
        className="sidebar",
    )
    main = html.Div(
        [dash.page_container],
        className="main",
    )
    return html.Div(
        [dcc.Location(id="url"), sidebar, main],
        className="app-shell",
    )


app = _build_app()
server = app.server  # for gunicorn / prod hosting later


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=8050)
