"""Narrative tile component used on the home hub.

Each tile is clickable and routes to its matching drill-down page. When data
is missing for the current reference date the tile renders greyed-out with
an explicit "no data" caption (per the missing-data policy).
"""
from __future__ import annotations

from dash import dcc, html

from app.components.tooltip import metric_tooltip_text
from core.captions import get_caption


def _format_rank(rank: int, total: int) -> str:
    if rank <= 0 or total <= 0:
        return "—"
    return f"{rank} / {total}"


def _format_delta(
    value: float | None,
    unit: str,
    direction: str = "higher_better",
) -> tuple[str, str]:
    """Return (text, css-class) for a delta-vs-peer-median line.

    The css-class reflects whether the delta is *favorable* for the bank,
    not just its mathematical sign. For ``higher_better`` metrics a
    positive delta is green; for ``lower_better`` metrics (e.g. the MREL
    requirement — where a lower figure is regulatory good news for the
    bank) a negative delta is shown in blue to flag "favorable but
    negative sign". ``neutral`` metrics (size — total assets, TREA,
    MREL stack in €) keep a grey delta since there is no favorable
    direction.
    """
    if value is None:
        return ("no peer median", "")
    if abs(value) < 0.001:
        return (f"= peer median ({unit})", "")
    sign = "+" if value > 0 else "−"
    magnitude = abs(value)
    if unit == "%":
        text = f"{sign}{magnitude * 100:.2f} pp vs peer median"
    elif unit == "pp":
        text = f"{sign}{magnitude * 100:.2f} pp vs peer median"
    elif unit == "€bn":
        text = f"{sign}€{magnitude / 1e9:.1f}bn vs peer median"
    else:
        text = f"{sign}{magnitude:.3f} vs peer median"

    if direction == "neutral":
        css = ""
    elif direction == "lower_better":
        # Below-median is favorable for the bank -> blue; above is unfavorable -> red.
        css = "favorable-inverted" if value < 0 else "unfavorable"
    else:  # "higher_better"
        css = "favorable" if value > 0 else "unfavorable"
    return text, css


def metric_tile(
    metric_key: str,
    *,
    href: str,
    rank: int,
    total: int,
    value: float | None,
    peer_median: float | None,
    has_data: bool,
    highlight: bool = False,
) -> dcc.Link:
    """Render a narrative tile with rank badge + delta vs peer median."""
    caption = get_caption(metric_key)

    classes = ["tile"]
    if not has_data:
        classes.append("tile-disabled")
    if highlight:
        classes.append("tile-highlight")

    if has_data and value is not None and peer_median is not None:
        delta = value - peer_median
    else:
        delta = None

    delta_text, delta_css = _format_delta(delta, caption.unit, caption.direction)
    delta_classes = "tile-delta"
    if delta_css:
        delta_classes += f" {delta_css}"

    body: list = [
        html.Div(caption.short_label, className="tile-title",
                 title=metric_tooltip_text(metric_key)),
    ]
    if has_data:
        body.extend([
            html.Div(_format_rank(rank, total), className="tile-rank"),
            html.Div(f"of BPM peer set · {caption.label}", className="tile-verdict",
                     style={"fontSize": "11px", "color": "#5b6572",
                            "fontWeight": 400, "marginTop": "2px"}),
            html.Div(delta_text, className=delta_classes),
        ])
    else:
        body.append(html.Div("No Pillar 3 data for this date",
                             className="tile-verdict",
                             style={"fontSize": "12px", "color": "#9aa4b1"}))

    return dcc.Link(
        body,
        href=href,
        className=" ".join(classes),
    )
