import math

import plotly.graph_objects as go

from ..models import Player
from .chart_style import (
    BAR_CORNER_RADIUS,
    NEUTRAL_PLAYER_COLOR,
    PRIMARY_PLAYER_COLOR,
    SECONDARY_PLAYER_COLOR,
    apply_common_chart_layout,
)
from .player_game_score_gap import GameScoreGap


def build_game_score_gap_chart(
    *,
    score_gaps: list[GameScoreGap],
    primary_player: Player,
    secondary_player: Player,
) -> go.Figure:
    """
    Build a floating bar chart for shared-game score gaps.

    Each bar begins at the lower player's actual score and extends to the
    higher player's actual score. This function receives prepared score-gap
    data and performs no database queries or score calculations.
    """
    if not score_gaps:
        raise ValueError(
            "At least one shared game is required to build the score-gap chart."
        )

    game_keys = [
        str(score_gap.game_id)
        for score_gap in score_gaps
    ]

    month_tick_values, month_tick_labels = _build_month_ticks(
        game_keys=game_keys,
        score_gaps=score_gaps,
    )

    bar_colors = []
    winner_labels = []
    hover_data = []

    for score_gap in score_gaps:
        if score_gap.winner is None:
            bar_colors.append(NEUTRAL_PLAYER_COLOR)
            winner_label = "Tie"
        elif score_gap.winner.id == primary_player.id:
            bar_colors.append(PRIMARY_PLAYER_COLOR)
            winner_label = primary_player.name
        elif score_gap.winner.id == secondary_player.id:
            bar_colors.append(SECONDARY_PLAYER_COLOR)
            winner_label = secondary_player.name
        else:
            raise ValueError(
                "Score-gap winner must be the primary player, "
                "secondary player, or None."
            )

        winner_labels.append(winner_label)

        hover_data.append(
            [
                score_gap.game_id,
                score_gap.date_played.strftime("%B %-d, %Y"),
                score_gap.primary_score,
                score_gap.secondary_score,
                score_gap.score_gap,
                winner_label,
            ]
        )

    low_scores = [
        score_gap.low_score
        for score_gap in score_gaps
    ]

    score_gap_values = [
        score_gap.score_gap
        for score_gap in score_gaps
    ]

    minimum_score = min(low_scores)
    maximum_score = max(
        score_gap.high_score
        for score_gap in score_gaps
    )

    y_axis_minimum = max(
        0,
        math.floor(minimum_score - 5),
    )

    y_axis_maximum = math.ceil(
        maximum_score + 5,
    )

    figure = go.Figure()

    # Legend-only traces explain the winner colors used by the score-gap bars.
    figure.add_trace(
        go.Bar(
            x=[None],
            y=[None],
            marker={
                "color": PRIMARY_PLAYER_COLOR,
            },
            name=f"{primary_player.name} wins",
            hoverinfo="skip",
            showlegend=True,
        )
    )

    figure.add_trace(
        go.Bar(
            x=[None],
            y=[None],
            marker={
                "color": SECONDARY_PLAYER_COLOR,
            },
            name=f"{secondary_player.name} wins",
            hoverinfo="skip",
            showlegend=True,
        )
    )

    figure.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode="markers",
            marker={
                "color": NEUTRAL_PLAYER_COLOR,
                "size": 10,
                "symbol": "square",
            },
            name="Tie",
            hoverinfo="skip",
            showlegend=True,
        )
    )

    figure.add_trace(
        go.Bar(
            x=game_keys,
            y=score_gap_values,
            base=low_scores,
            marker={
                "color": bar_colors,
                "cornerradius": BAR_CORNER_RADIUS,
            },
            customdata=hover_data,
            hovertemplate=(
                "<b>Game %{customdata[0]}</b><br>"
                "%{customdata[1]}<br>"
                f"{primary_player.name}: %{{customdata[2]}}<br>"
                f"{secondary_player.name}: %{{customdata[3]}}<br>"
                "Score Gap: %{customdata[4]}<br>"
                "Winner: %{customdata[5]}"
                "<extra></extra>"
            ),
            showlegend=False,
        )
    )

    # A zero-height bar is not visibly rendered by Plotly. Overlay a neutral
    # marker at the tied score so tied games remain visible and hoverable while
    # preserving the true score gap of zero.
    tie_labels = []
    tie_scores = []
    tie_hover_data = []

    for game_key, score_gap, hover_row in zip(
        game_keys,
        score_gaps,
        hover_data,
    ):
        if score_gap.score_gap == 0:
            tie_labels.append(game_key)
            tie_scores.append(score_gap.low_score)
            tie_hover_data.append(hover_row)

    if tie_labels:
        figure.add_trace(
            go.Scatter(
                x=tie_labels,
                y=tie_scores,
                mode="markers",
                marker={
                    "color": NEUTRAL_PLAYER_COLOR,
                    "size": 10,
                    "symbol": "line-ew",
                    "line": {
                        "color": NEUTRAL_PLAYER_COLOR,
                        "width": 4,
                    },
                },
                customdata=tie_hover_data,
                hovertemplate=(
                    "<b>Game %{customdata[0]}</b><br>"
                    "%{customdata[1]}<br>"
                    f"{primary_player.name}: %{{customdata[2]}}<br>"
                    f"{secondary_player.name}: %{{customdata[3]}}<br>"
                    "Score Gap: %{customdata[4]}<br>"
                    "Winner: %{customdata[5]}"
                    "<extra></extra>"
                ),
                showlegend=False,
            )
        )

    figure.update_layout(
        title={
            "text": (
                f"{primary_player.name} vs {secondary_player.name}"
                " — Game Score Gap"
            ),
            "x": 0.5,
            "xanchor": "center",
        },
        xaxis={
            "title": None,
            "type": "category",
            "categoryorder": "array",
            "categoryarray": game_keys,
            "tickvals": month_tick_values,
            "ticktext": month_tick_labels,
            "tickangle": 0,
            "fixedrange": True,
        },
        yaxis={
            "title": "Score",
            "range": [
                y_axis_minimum,
                y_axis_maximum,
            ],
            "fixedrange": True,
        },
        bargap=0.25,
        hovermode="closest",
    )

    apply_common_chart_layout(
        figure=figure,
    )

    return figure

def _build_month_ticks(
    *,
    game_keys: list[str],
    score_gaps: list[GameScoreGap],
) -> tuple[list[str], list[str]]:
    """
    Build x-axis tick positions and month labels.

    Each month is labeled at the first game played during that month.
    """
    tick_values = []
    tick_labels = []

    previous_month = None

    for game_key, score_gap in zip(
        game_keys,
        score_gaps,
    ):
        month_key = (
            score_gap.date_played.year,
            score_gap.date_played.month,
        )

        if month_key == previous_month:
            continue

        tick_values.append(game_key)
        tick_labels.append(
            score_gap.date_played.strftime("%b ’%y")
        )

        previous_month = month_key

    return tick_values, tick_labels