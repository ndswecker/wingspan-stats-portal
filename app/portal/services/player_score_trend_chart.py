import plotly.graph_objects as go
import math

from ..models import Player
from .player_score_trends import MonthlyScoreAverage
from .player_score_distribution import (
    ScoreDistribution,
    ScoreDistributionComparison,
)
from .chart_style import (
    PRIMARY_PLAYER_COLOR,
    SECONDARY_PLAYER_COLOR,
    PRIMARY_BAR_OPACITY,
    SECONDARY_BAR_OPACITY,
    PRIMARY_OVERLAY_BAR_WIDTH_RATIO,
    SECONDARY_OVERLAY_BAR_WIDTH_RATIO,
    BAR_CORNER_RADIUS,
    apply_common_chart_layout,
)


def build_monthly_score_chart(
    *,
    monthly_scores: list[MonthlyScoreAverage],
    player: Player,
    game_type_label: str,
    period_label: str,
) -> go.Figure:
    """
    Build a monthly average-score column chart.

    This function receives prepared monthly data and performs no database
    queries or statistical calculations. In single-player mode, the selected
    player receives the shared Primary Player chart styling.
    """
    use_year_in_labels = period_label == "Last 12 Months"

    month_labels = [
        _build_month_label(
            monthly_score=monthly_score,
            include_year=use_year_in_labels,
        )
        for monthly_score in monthly_scores
    ]

    average_scores = [
        monthly_score.average_score
        for monthly_score in monthly_scores
    ]

    visible_scores = [
        score
        for score in average_scores
        if score is not None
    ]

    minimum_score = min(visible_scores)
    maximum_score = max(visible_scores)

    y_axis_minimum = max(
        50,
        math.floor(minimum_score - 5),
    )

    y_axis_maximum = math.ceil(
        maximum_score + 5,
    )

    hover_data = [
        [
            monthly_score.month_start.strftime("%B %Y"),
            monthly_score.games_played,
        ]
        for monthly_score in monthly_scores
    ]

    score_labels = []

    for score in average_scores:
        if score is None:
            score_labels.append("")
        else:
            score_labels.append(
                f"{score:.1f}"
            )

    figure = go.Figure(
        data=[
            go.Bar(
                x=month_labels,
                y=average_scores,
                text=score_labels,
                textposition="outside",
                opacity=PRIMARY_BAR_OPACITY,
                marker={
                    "color": PRIMARY_PLAYER_COLOR,
                },
                customdata=hover_data,
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>"
                    "Average Score: %{y:.1f}<br>"
                    "Games Played: %{customdata[1]}"
                    "<extra></extra>"
                ),
            )
        ]
    )

    figure.update_layout(
        title={
            "text": (
                f"{player.name} — {game_type_label}"
                f"<br><sup>{period_label}</sup>"
            ),
            "x": 0.5,
            "xanchor": "center",
        },
        xaxis={
            "title": None,
            "type": "category",
            "categoryorder": "array",
            "categoryarray": month_labels,
            "tickangle": 45,
            "fixedrange": True,
        },
        yaxis={
            "title": "Average Score",
            "range": [
                y_axis_minimum,
                y_axis_maximum,
            ],
            "fixedrange": True,
        },
        showlegend=False,
        barcornerradius=BAR_CORNER_RADIUS,
    )

    apply_common_chart_layout(
        figure=figure,
    )

    return figure

def build_monthly_score_comparison_chart(
    *,
    primary_monthly_scores: list[MonthlyScoreAverage],
    secondary_monthly_scores: list[MonthlyScoreAverage],
    primary_player: Player,
    secondary_player: Player,
    game_type_label: str,
    period_label: str,
) -> go.Figure:
    """
    Build an overlapping monthly average-score comparison chart.

    Both players share the same monthly axis and score scale. The Secondary
    Player is rendered as the wider background series while the Primary
    Player is rendered as the narrower foreground series using the shared
    Wingspan chart styling.

    This function receives prepared monthly data and performs no database
    queries or statistical calculations.
    """
    if len(primary_monthly_scores) != len(secondary_monthly_scores):
        raise ValueError(
            "Primary and secondary monthly score lists must cover the same period."
        )

    for primary_score, secondary_score in zip(
        primary_monthly_scores,
        secondary_monthly_scores,
    ):
        if primary_score.month_start != secondary_score.month_start:
            raise ValueError(
                "Primary and secondary monthly scores must contain matching months."
            )

    month_labels = [
        monthly_score.month_start.strftime("%b \u2019%y")
        for monthly_score in primary_monthly_scores
    ]

    primary_average_scores = [
        monthly_score.average_score
        for monthly_score in primary_monthly_scores
    ]

    secondary_average_scores = [
        monthly_score.average_score
        for monthly_score in secondary_monthly_scores
    ]

    visible_scores = [
        score
        for score in (
            primary_average_scores
            + secondary_average_scores
        )
        if score is not None
    ]

    if not visible_scores:
        raise ValueError(
            "At least one monthly score is required to build the comparison chart."
        )

    minimum_score = min(visible_scores)
    maximum_score = max(visible_scores)

    y_axis_minimum = max(
        50,
        math.floor(minimum_score - 5),
    )

    y_axis_maximum = math.ceil(
        maximum_score + 5,
    )

    primary_hover_data = [
        [
            monthly_score.month_start.strftime("%B %Y"),
            monthly_score.games_played,
        ]
        for monthly_score in primary_monthly_scores
    ]

    secondary_hover_data = [
        [
            monthly_score.month_start.strftime("%B %Y"),
            monthly_score.games_played,
        ]
        for monthly_score in secondary_monthly_scores
    ]

    primary_score_labels = [
        (
            ""
            if score is None
            else f"{score:.1f}"
        )
        for score in primary_average_scores
    ]

    figure = go.Figure()

    # The Secondary Player is added first as the wider, lighter background
    # series so the Primary Player remains visually dominant.
    figure.add_trace(
        go.Bar(
            x=month_labels,
            y=secondary_average_scores,
            width=SECONDARY_OVERLAY_BAR_WIDTH_RATIO,
            opacity=SECONDARY_BAR_OPACITY,
            marker={
                "color": SECONDARY_PLAYER_COLOR,
            },
            name=secondary_player.name,
            customdata=secondary_hover_data,
            hovertemplate=(
                f"<b>{secondary_player.name}</b><br>"
                "<b>%{customdata[0]}</b><br>"
                "Average Score: %{y:.1f}<br>"
                "Games Played: %{customdata[1]}"
                "<extra></extra>"
            ),
        )
    )

    # The Primary Player is added second as the narrower foreground series.
    # Persistent labels remain exclusive to the Primary Player.
    figure.add_trace(
        go.Bar(
            x=month_labels,
            y=primary_average_scores,
            width=PRIMARY_OVERLAY_BAR_WIDTH_RATIO,
            opacity=PRIMARY_BAR_OPACITY,
            marker={
                "color": PRIMARY_PLAYER_COLOR,
            },
            name=primary_player.name,
            text=primary_score_labels,
            textposition="outside",
            customdata=primary_hover_data,
            hovertemplate=(
                f"<b>{primary_player.name}</b><br>"
                "<b>%{customdata[0]}</b><br>"
                "Average Score: %{y:.1f}<br>"
                "Games Played: %{customdata[1]}"
                "<extra></extra>"
            ),
        )
    )

    figure.update_layout(
        title={
            "text": (
                f"{primary_player.name} vs {secondary_player.name}"
                f" — {game_type_label}"
            ),
            "x": 0.5,
            "xanchor": "center",
        },
        barmode="overlay",
        barcornerradius=BAR_CORNER_RADIUS,
        xaxis={
            "title": None,
            "type": "category",
            "categoryorder": "array",
            "categoryarray": month_labels,
            "tickangle": 45,
            "fixedrange": True,
        },
        yaxis={
            "title": "Average Score",
            "range": [
                y_axis_minimum,
                y_axis_maximum,
            ],
            "fixedrange": True,
        },
    )

    apply_common_chart_layout(
        figure=figure,
    )

    return figure

def _build_month_label(
    *,
    monthly_score: MonthlyScoreAverage,
    include_year: bool,
) -> str:
    if include_year:
        return monthly_score.month_start.strftime("%b %y")

    return monthly_score.month_abbreviation

