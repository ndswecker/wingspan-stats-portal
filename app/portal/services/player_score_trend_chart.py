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

    Player 1 is rendered as the narrower foreground series.
    Player 2 is rendered as the wider background series.

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

    # Player 2 is added first so it remains behind Player 1.
    figure.add_trace(
        go.Bar(
            x=month_labels,
            y=secondary_average_scores,
            width=0.75,
            opacity=0.40,
            name=f"P2 — {secondary_player.name}",
            customdata=secondary_hover_data,
            hovertemplate=(
                f"<b>P2 — {secondary_player.name}</b><br>"
                "<b>%{customdata[0]}</b><br>"
                "Average Score: %{y:.1f}<br>"
                "Games Played: %{customdata[1]}"
                "<extra></extra>"
            ),
        )
    )

    # Player 1 is added second so it renders in the foreground.
    figure.add_trace(
        go.Bar(
            x=month_labels,
            y=primary_average_scores,
            width=0.42,
            name=f"P1 — {primary_player.name}",
            text=primary_score_labels,
            textposition="outside",
            customdata=primary_hover_data,
            hovertemplate=(
                f"<b>P1 — {primary_player.name}</b><br>"
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
                f"<br><sup>{period_label}</sup>"
            ),
            "x": 0.5,
            "xanchor": "center",
        },
        barmode="overlay",
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
        autosize=True,
        margin={
            "l": 60,
            "r": 20,
            "t": 100,
            "b": 60,
        },
        hoverlabel={
            "align": "left",
        },
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "center",
            "x": 0.5,
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