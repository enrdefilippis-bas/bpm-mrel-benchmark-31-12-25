"""Visual theme — professional navy / amber / red palette.

Shared by every page and every Plotly figure so the look stays consistent
across the app.
"""
from __future__ import annotations

from typing import Final


# Core palette
NAVY = "#0b2545"           # primary background / hero text
NAVY_DEEP = "#061629"      # page background
NAVY_SOFT = "#13315c"      # sidebar background
STEEL = "#4a6a8a"          # axis / muted text
MIST = "#e6ecf2"           # card background
CLOUD = "#f5f7fa"          # page card accent
WHITE = "#ffffff"

AMBER = "#e6a817"          # secondary accent (requirement line, warning)
AMBER_SOFT = "#f3c96a"
RED = "#c0362c"            # BPM highlight / unfavorable delta
RED_SOFT = "#e8857d"
TEAL = "#2e7d7d"           # peer aggregate
GREEN = "#2e7d4f"          # surplus positive / favorable delta
BLUE = "#1e5bb8"           # favorable-inverted delta (e.g. below-median req)

GREY_200 = "#d5dae0"
GREY_400 = "#9aa4b1"
GREY_600 = "#5b6572"
GREY_800 = "#1f2937"

# Semantic roles
BPM_COLOR: Final[str] = RED
PEER_COLOR: Final[str] = STEEL
REQUIREMENT_COLOR: Final[str] = AMBER
SURPLUS_POSITIVE: Final[str] = GREEN
SURPLUS_NEGATIVE: Final[str] = RED

# Plotly layout defaults
PLOT_BG = WHITE
PAPER_BG = WHITE
FONT_FAMILY = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"

PLOTLY_LAYOUT: Final[dict] = {
    "paper_bgcolor": PAPER_BG,
    "plot_bgcolor": PLOT_BG,
    "font": {"family": FONT_FAMILY, "color": GREY_800, "size": 12},
    "title": {"font": {"family": FONT_FAMILY, "color": NAVY, "size": 16}, "x": 0.0},
    "margin": {"l": 48, "r": 24, "t": 48, "b": 40},
    "hoverlabel": {
        "bgcolor": NAVY,
        "bordercolor": NAVY,
        "font": {"family": FONT_FAMILY, "color": WHITE, "size": 12},
    },
    "colorway": [NAVY, STEEL, TEAL, AMBER, RED, GREEN, GREY_600],
    "xaxis": {"gridcolor": GREY_200, "zerolinecolor": GREY_200},
    "yaxis": {"gridcolor": GREY_200, "zerolinecolor": GREY_200},
}


def apply_layout(fig):
    """Attach the shared layout defaults to a Plotly figure in-place."""
    fig.update_layout(**PLOTLY_LAYOUT)
    return fig


# CSS snippets injected into index_string
GLOBAL_CSS: Final[str] = f"""
<style>
  body {{
    background: {NAVY_DEEP};
    margin: 0;
    color: {GREY_800};
    font-family: {FONT_FAMILY};
  }}
  .app-shell {{
    display: flex;
    min-height: 100vh;
  }}
  .sidebar {{
    width: 260px;
    background: {NAVY_SOFT};
    color: {WHITE};
    padding: 24px 20px;
    box-shadow: 2px 0 8px rgba(0,0,0,0.15);
  }}
  .sidebar h1 {{
    font-size: 18px;
    margin: 0 0 4px 0;
    color: {WHITE};
  }}
  .sidebar .subtitle {{
    color: {GREY_400};
    font-size: 12px;
    margin-bottom: 28px;
  }}
  .sidebar .nav-link {{
    display: block;
    padding: 8px 10px;
    margin: 2px 0;
    color: {MIST};
    text-decoration: none;
    border-radius: 4px;
    font-size: 13px;
  }}
  .sidebar .nav-link:hover {{ background: rgba(255,255,255,0.06); }}
  .sidebar .nav-link.active {{
    background: rgba(230, 168, 23, 0.16);
    color: {AMBER_SOFT};
    border-left: 3px solid {AMBER};
    padding-left: 7px;
  }}
  .sidebar .section-title {{
    color: {GREY_400};
    font-size: 10px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin: 24px 0 8px 0;
  }}
  .sidebar .control-label {{
    color: {MIST};
    font-size: 12px;
    margin: 12px 0 6px 0;
  }}
  .main {{
    flex: 1;
    padding: 28px 36px;
    background: {CLOUD};
    overflow-x: auto;
  }}
  .page-header h2 {{
    color: {NAVY};
    margin: 0 0 4px 0;
    font-size: 22px;
  }}
  .page-header .caption {{
    color: {GREY_600};
    font-size: 13px;
    margin-bottom: 20px;
  }}
  .tile-grid {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
    margin-bottom: 24px;
  }}
  .tile {{
    background: {WHITE};
    border-radius: 6px;
    padding: 14px 16px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    border-left: 3px solid {STEEL};
    cursor: pointer;
    transition: transform 0.08s ease-in-out, box-shadow 0.08s ease-in-out;
    text-decoration: none;
    color: inherit;
    display: block;
  }}
  .tile:hover {{
    transform: translateY(-1px);
    box-shadow: 0 3px 8px rgba(0,0,0,0.10);
  }}
  .tile.tile-disabled {{
    opacity: 0.55;
    border-left-color: {GREY_400};
    cursor: default;
  }}
  .tile.tile-highlight {{ border-left-color: {RED}; }}
  .tile .tile-title {{
    color: {GREY_600};
    font-size: 11px;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    margin-bottom: 4px;
  }}
  .tile .tile-verdict {{
    color: {NAVY};
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 6px;
  }}
  .tile .tile-rank {{
    font-size: 22px;
    color: {NAVY};
    font-weight: 600;
    line-height: 1.1;
  }}
  .tile .tile-delta {{
    font-size: 12px;
    color: {GREY_600};
    margin-top: 2px;
  }}
  .tile .tile-delta.favorable {{ color: {GREEN}; }}
  .tile .tile-delta.unfavorable {{ color: {RED}; }}
  .tile .tile-delta.favorable-inverted {{ color: {BLUE}; }}
  /* legacy aliases — kept so old screenshots/tests keep working */
  .tile .tile-delta.pos {{ color: {GREEN}; }}
  .tile .tile-delta.neg {{ color: {RED}; }}
  .card {{
    background: {WHITE};
    border-radius: 6px;
    padding: 20px 24px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    margin-bottom: 16px;
  }}
  .card h3 {{
    color: {NAVY};
    margin: 0 0 4px 0;
    font-size: 15px;
  }}
  .card .card-caption {{
    color: {GREY_600};
    font-size: 12px;
    margin-bottom: 12px;
  }}
  .meta-line {{
    color: {GREY_600};
    font-size: 11px;
    margin-top: 6px;
    font-style: italic;
  }}
  .export-bar {{
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 0 0 12px 0;
  }}
  .export-btn {{
    background: {NAVY};
    color: {WHITE};
    border: 1px solid {NAVY};
    border-radius: 4px;
    padding: 6px 14px;
    font-size: 12px;
    font-family: inherit;
    cursor: pointer;
    letter-spacing: 0.02em;
  }}
  .export-btn:hover {{
    background: {NAVY_SOFT};
    border-color: {NAVY_SOFT};
  }}
  .export-btn:active {{
    background: {STEEL};
  }}
  .export-hint {{
    color: {GREY_400};
    font-size: 11px;
  }}
  .dcc-dropdown .Select-control {{
    background: {NAVY} !important;
    border-color: {STEEL} !important;
    color: {WHITE} !important;
  }}
</style>
"""
