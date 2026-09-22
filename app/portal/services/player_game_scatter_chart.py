
import plotly.graph_objects as go

from datetime import date

from django.db.models import QuerySet

from ..models import GameResult, Player
from .chart_style import (
    PRIMARY_PLAYER_COLOR,
    SECONDARY_PLAYER_COLOR,
    PRIMARY_BAR_OPACITY,
    SECONDARY_BAR_OPACITY,
    apply_common_chart_layout,
)


def _build_monthly_game_counts(
    *,
    game_results: list[GameResult],
    start_date: date,
    end_date: date,
) -> dict[date, int]:
    """
    Build monthly game counts across the complete date range.
    """

    monthly_game_counts = {}

    current_year = start_date.year
    current_month = start_date.month

    while (
        current_year < end_date.year
        or (
            current_year == end_date.year
            and current_month <= end_date.month
        )
    ):
        month_date = date(
            current_year,
            current_month,
            15,
        )

        monthly_game_counts[month_date] = 0

        if current_month == 12:
            current_year += 1
            current_month = 1
        else:
            current_month += 1

    for game_result in game_results:
        game_date = game_result.game.date_played

        month_date = date(
            game_date.year,
            game_date.month,
            15,
        )

        monthly_game_counts[month_date] += 1

    return monthly_game_counts


def build_game_scatter_chart(
        *,
        primary_game_results: QuerySet[GameResult],
        secondary_game_results: QuerySet[GameResult] | None = None,
        primary_player: Player,
        secondary_player: Player | None = None,
        start_date: date,
        end_date: date,
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

    primary_monthly_game_counts = _build_monthly_game_counts(
        game_results=primary_results,
        start_date=start_date,
        end_date=end_date,
    )

    secondary_monthly_game_counts = {}

    if secondary_results is not None:
        secondary_monthly_game_counts = _build_monthly_game_counts(
            game_results=secondary_results,
            start_date=start_date,
            end_date=end_date,
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

    figure.add_trace(
        go.Scatter(
            x=list(primary_monthly_game_counts.keys()),
            y=list(primary_monthly_game_counts.values()),
            mode="lines+markers",
            line={
                "color": PRIMARY_PLAYER_COLOR,
                "shape": "spline",
                "width": 2,
            },
            marker={
                "color": PRIMARY_PLAYER_COLOR,
                "size": 6,
            },
            name=f"{primary_player.name} Games Played",
            yaxis="y2",
            hovertemplate=(
                f"<b>{primary_player.name}</b><br>"
                "Month: %{x|%B %Y}<br>"
                "Games Played: %{y}"
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

        figure.add_trace(
            go.Scatter(
                x=list(secondary_monthly_game_counts.keys()),
                y=list(secondary_monthly_game_counts.values()),
                mode="lines+markers",
                line={
                    "color": SECONDARY_PLAYER_COLOR,
                    "shape": "spline",
                    "width": 2,
                },
                marker={
                    "color": SECONDARY_PLAYER_COLOR,
                    "size": 6,
                },
                name=f"{secondary_player.name} Games Played",
                yaxis="y2",
                hovertemplate=(
                    f"<b>{secondary_player.name}</b><br>"
                    "Month: %{x|%B %Y}<br>"
                    "Games Played: %{y}"
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
        yaxis2={
            "title": "Games Played",
            "overlaying": "y",
            "side": "right",
            "fixedrange": True,
            "rangemode": "tozero",
        },
        showlegend=False,
    )

    apply_common_chart_layout(
        figure=figure,
    )

    return figure