import plotly.graph_objects as go
import math

from ..models import Player
from .player_score_trends import MonthlyScoreAverage


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
    queries or statistical calculations.
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

    y_axis_minimum = max(50, math.floor(minimum_score - 5))
    y_axis_maximum = math.ceil(maximum_score +5)

    hover_data = [
        [
            monthly_score.month_start.strftime("%B %Y"),
            monthly_score.games_played,
        ]
        for monthly_score in monthly_scores
    ]

    score_labels=[]
    for score in average_scores:
        if score is None:
            score_labels.append("")
        else:
            score_labels.append(f"{score:.1f}")

    figure = go.Figure(
        data=[
            go.Bar(
                x=month_labels,
                y=average_scores,
                text=score_labels,
                textposition="outside",
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
        dragmode=False,
        showlegend=False,
        autosize=True,
        margin={
            "l": 60,
            "r": 20,
            "t": 80,
            "b": 60,
        },
        hoverlabel={
            "align": "left",
        },
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