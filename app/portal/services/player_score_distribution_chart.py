import plotly.graph_objects as go

from ..models import Player
from .player_score_distribution import ScoreDistribution


def build_score_distribution_chart(
    *,
    score_distribution: ScoreDistribution,
) -> go.Figure:
    """
    Build a score-distribution histogram with a fitted normal reference curve.

    This function receives already-calculated distribution data and performs
    no database queries or statistical calculations.
    """
    histogram_bins = score_distribution.histogram_bins

    if not histogram_bins:
        raise ValueError(
            "Histogram bins are required to build a score distribution chart."
        )

    # Histogram bins use a consistent fixed width.
    # The width is needed to scale probability density values so the
    # normal curve can be compared visually against game-count bars.
    bin_width = (
        histogram_bins[0].upper_bound
        - histogram_bins[0].lower_bound
    )

    bin_labels = [
        (
            f"{histogram_bin.lower_bound}-"
            f"{histogram_bin.upper_bound - 1}"
        )
        for histogram_bin in histogram_bins
    ]

    bin_centers = [
        (
            histogram_bin.lower_bound
            + histogram_bin.upper_bound
        ) / 2
        for histogram_bin in histogram_bins
    ]

    games_played_by_bin = [
        histogram_bin.games_played
        for histogram_bin in histogram_bins
    ]

    figure = go.Figure()

    figure.add_trace(
        go.Bar(
            x=bin_centers,
            y=games_played_by_bin,
            width=bin_width,
            customdata=bin_labels,
            name="Observed Scores",
            hovertemplate=(
                "<b>Score Range: %{customdata}</b><br>"
                "Games Played: %{y}"
                "<extra></extra>"
            ),
        )
    )

    if score_distribution.normal_curve_points:
        curve_scores = [
            point.score
            for point in score_distribution.normal_curve_points
        ]

        # Probability density does not naturally use the same scale as
        # histogram game counts. Multiply density by sample size and bin
        # width so the reference curve is visually comparable to the bars.
        scaled_curve_values = [
            (
                point.density
                * score_distribution.games_played
                * bin_width
            )
            for point in score_distribution.normal_curve_points
        ]

        figure.add_trace(
            go.Scatter(
                x=curve_scores,
                y=scaled_curve_values,
                mode="lines",
                name="Normal Reference",
                hovertemplate=(
                    "Score: %{x:.0f}<br>"
                    "Reference Count: %{y:.1f}"
                    "<extra></extra>"
                ),
            )
        )

    figure.update_layout(
        xaxis={
            "title": "Score",
            "tickmode": "array",
            "tickvals": bin_centers,
            "ticktext": bin_labels,
            "tickangle": 45,
            "fixedrange": True,
        },
        yaxis={
            "title": "Games Played",
            "rangemode": "tozero",
            "fixedrange": True,
        },
        dragmode=False,
        autosize=True,
        bargap=0.05,
        margin={
            "l": 60,
            "r": 20,
            "t": 70,
            "b": 90,
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