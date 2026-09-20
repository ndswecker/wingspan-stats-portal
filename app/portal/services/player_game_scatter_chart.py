
import plotly.graph_objects as go
from django.db.models import QuerySet

from ..models import GameResult, Player
from .chart_style import (
    PRIMARY_PLAYER_COLOR,
    SECONDARY_PLAYER_COLOR,
    PRIMARY_BAR_OPACITY,
    SECONDARY_BAR_OPACITY,
    apply_common_chart_layout,
)


def build_game_scatter_chart(
        *,
        primary_game_results: QuerySet[GameResult],
        secondary_game_results: QuerySet[GameResult] | None = None,
        primary_player: Player,
        secondary_player: Player | None = None,
) -> go.Figure:
    """
    Build an individual-game score scatter chart.
    Each marker represents one game result positioned by the game's actual
    date and the player's score.
    """

    primary_results = list(
        primary_game_results.order_by(
            "game__date_played",
            "game_id",
        )
    )

    secondary_results = []

    if secondary_game_results is not None:
        secondary_results = list(
            secondary_game_results.order_by(
                "game__date_played",
                "game_id",
            )
        )

    primary_dates = [
        game_result.game.date_played
        for game_result in primary_results
    ]

    primary_scores = [
        game_result.score
        for game_result in primary_results
    ]

    secondary_dates = [
        game_result.game.date_played
        for game_result in secondary_results
    ]

    secondary_scores = [
        game_result.score
        for game_result in secondary_results
    ]

    figure = go.Figure()

    figure.add_trace(
        go.Scatter(
            x=primary_dates,
            y=primary_scores,
            mode="markers",
            marker={
                "color": PRIMARY_PLAYER_COLOR,
                "size": 9,
            },
            opacity=PRIMARY_BAR_OPACITY,
            name=primary_player.name,
            hovertemplate=(
                f"<b>{primary_player.name}</b><br>"
                "Date: %{x|%B %d, %Y}<br>"
                "Score: %{y}"
                "<extra></extra>"
            ),
        )
    )

    if secondary_player is not None:
        figure.add_trace(
            go.Scatter(
                x=secondary_dates,
                y=secondary_scores,
                mode="markers",
                marker={
                    "color": SECONDARY_PLAYER_COLOR,
                    "size": 7,
                },
                opacity=SECONDARY_BAR_OPACITY,
                name=secondary_player.name,
                hovertemplate=(
                    f"<b>{secondary_player.name}</b><br>"
                    "Date: %{x|%B %d, %Y}<br>"
                    "Score: %{y}"
                    "<extra></extra>"
                ),
            )
        )

    figure.update_layout(
        xaxis={
            "title": None,
            "type": "date",
            "fixedrange": True,
        },
        yaxis={
            "title": "Score",
            "fixedrange": True,
        },
        showlegend=secondary_player is not None,
    )

    apply_common_chart_layout(
        figure=figure,
    )

    return figure