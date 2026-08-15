"""
Shared Plotly styling for Wingspan Portal charts.

Chart colors and visual treatments are assigned by semantic role rather than
by player identity. A player displayed as the Primary Player should therefore
receive the same visual treatment across every chart, while a Secondary Player
receives the corresponding comparison treatment.

This module is intentionally centralized so chart presentation can evolve
without requiring styling changes throughout individual chart builders.
"""

import plotly.graph_objects as go


# ---------------------------------------------------------------------------
# Player colors
# ---------------------------------------------------------------------------

# Temporary starting colors. These are intentionally centralized so the
# application's palette can be changed without modifying individual charts.
PRIMARY_PLAYER_COLOR = "#D94F70"
SECONDARY_PLAYER_COLOR = "#4C78C2"


# ---------------------------------------------------------------------------
# Bar presentation
# ---------------------------------------------------------------------------

PRIMARY_BAR_OPACITY = 1.0
SECONDARY_BAR_OPACITY = 0.40

# Overlapping charts use a wider Secondary bar behind a narrower Primary bar.
PRIMARY_OVERLAY_BAR_WIDTH_RATIO = 0.55
SECONDARY_OVERLAY_BAR_WIDTH_RATIO = 0.90

# Rounded corners provide some visual character without introducing
# misleading three-dimensional effects.
BAR_CORNER_RADIUS = 6


# ---------------------------------------------------------------------------
# Line presentation
# ---------------------------------------------------------------------------

PRIMARY_LINE_WIDTH = 2.5
SECONDARY_LINE_WIDTH = 2.0

PRIMARY_LINE_OPACITY = 1.0
SECONDARY_LINE_OPACITY = 0.65


# ---------------------------------------------------------------------------
# Common chart presentation
# ---------------------------------------------------------------------------

LEGEND = {
    "orientation": "h",
    "yanchor": "bottom",
    "y": 1.02,
    "xanchor": "center",
    "x": 0.5,
}

HOVER_LABEL = {
    "align": "left",
}

DEFAULT_MARGIN = {
    "l": 60,
    "r": 20,
    "t": 70,
    "b": 90,
}


def apply_common_chart_layout(
    *,
    figure: go.Figure,
) -> None:
    """
    Apply presentation rules shared by Wingspan Portal Plotly charts.

    Individual chart builders remain responsible for chart-specific axis
    configuration, titles, ranges, and data presentation.
    """
    figure.update_layout(
        dragmode=False,
        autosize=True,
        hoverlabel=HOVER_LABEL,
        legend=LEGEND,
        margin=DEFAULT_MARGIN,
    )