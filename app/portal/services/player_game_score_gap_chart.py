import math

import plotly.graph_objects as go

from django.urls import reverse

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

    game_labels = [
        f"{score_gap.game_id} "
        f"{score_gap.date_played.month}/{score_gap.date_played.day}/"
        f"{score_gap.date_played.strftime('%y')}"
        for score_gap in score_gaps
    ]

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
                reverse(
                    "portal:game-detail",
                    kwargs={"pk": score_gap.game_id},
                ),
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

    figure.add_trace(
        go.Bar(
            x=game_labels,
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

    for game_label, score_gap, hover_row in zip(
        game_labels,
        score_gaps,
        hover_data,
    ):
        if score_gap.score_gap == 0:
            tie_labels.append(game_label)
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
            "categoryarray": game_labels,
            "tickangle": 45,
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
