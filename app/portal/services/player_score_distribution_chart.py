import plotly.graph_objects as go

from ..models import Player
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
    PRIMARY_LINE_WIDTH,
    SECONDARY_LINE_WIDTH,
    PRIMARY_LINE_OPACITY,
    SECONDARY_LINE_OPACITY,
    apply_common_chart_layout,
)

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

def build_score_distribution_comparison_chart(
    *,
    score_distribution_comparison: ScoreDistributionComparison,
    primary_player: Player,
    secondary_player: Player,
) -> go.Figure:
    """
    Build an overlapping score-distribution comparison chart.

    Both players share the same score bins and density axis. The Secondary
    Player is rendered as the wider background histogram while the Primary
    Player is rendered as the narrower foreground histogram. Each player
    retains an independently fitted normal reference curve using the same
    semantic styling as that player's histogram bars.
    """
    histogram_bins = score_distribution_comparison.histogram_bins

    if not histogram_bins:
        raise ValueError(
            "Histogram bins are required to build a score distribution comparison chart."
        )

    # Every comparison bin represents the same score interval for both
    # players, allowing the two histogram traces to occupy one x-position.
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

    primary_densities = [
        histogram_bin.primary_density
        for histogram_bin in histogram_bins
    ]

    secondary_densities = [
        histogram_bin.secondary_density
        for histogram_bin in histogram_bins
    ]

    # Counts and percentages remain available for human-readable hover
    # details even though density determines the visual bar height.
    primary_hover_data = [
        [
            bin_label,
            histogram_bin.primary_games_played,
            histogram_bin.primary_percentage,
        ]
        for bin_label, histogram_bin in zip(
            bin_labels,
            histogram_bins,
        )
    ]

    secondary_hover_data = [
        [
            bin_label,
            histogram_bin.secondary_games_played,
            histogram_bin.secondary_percentage,
        ]
        for bin_label, histogram_bin in zip(
            bin_labels,
            histogram_bins,
        )
    ]

    figure = go.Figure()

    # The Secondary Player is rendered first as the wider, lighter
    # background histogram.
    figure.add_trace(
        go.Bar(
            x=bin_centers,
            y=secondary_densities,
            width=(
                bin_width
                * SECONDARY_OVERLAY_BAR_WIDTH_RATIO
            ),
            opacity=SECONDARY_BAR_OPACITY,
            marker={
                "color": SECONDARY_PLAYER_COLOR,
            },
            customdata=secondary_hover_data,
            name=secondary_player.name,
            hovertemplate=(
                f"<b>{secondary_player.name}</b><br>"
                "<b>Score Range: %{customdata[0]}</b><br>"
                "Games: %{customdata[1]}<br>"
                "Share of Games: %{customdata[2]:.1f}%"
                "<extra></extra>"
            ),
        )
    )

    # The Primary Player is rendered second as the narrower foreground
    # histogram using the primary-player visual treatment.
    figure.add_trace(
        go.Bar(
            x=bin_centers,
            y=primary_densities,
            width=(
                bin_width
                * PRIMARY_OVERLAY_BAR_WIDTH_RATIO
            ),
            opacity=PRIMARY_BAR_OPACITY,
            marker={
                "color": PRIMARY_PLAYER_COLOR,
            },
            customdata=primary_hover_data,
            name=primary_player.name,
            hovertemplate=(
                f"<b>{primary_player.name}</b><br>"
                "<b>Score Range: %{customdata[0]}</b><br>"
                "Games: %{customdata[1]}<br>"
                "Share of Games: %{customdata[2]:.1f}%"
                "<extra></extra>"
            ),
        )
    )

    # Each normal curve already contains probability-density values, so no
    # sample-size or bin-width scaling is needed in comparison mode.
    if score_distribution_comparison.secondary_normal_curve_points:
        secondary_curve_scores = [
            point.score
            for point
            in score_distribution_comparison.secondary_normal_curve_points
        ]

        secondary_curve_densities = [
            point.density
            for point
            in score_distribution_comparison.secondary_normal_curve_points
        ]

        figure.add_trace(
            go.Scatter(
                x=secondary_curve_scores,
                y=secondary_curve_densities,
                mode="lines",
                name=secondary_player.name,
                showlegend=False,
                opacity=SECONDARY_LINE_OPACITY,
                line={
                    "color": SECONDARY_PLAYER_COLOR,
                    "width": SECONDARY_LINE_WIDTH,
                },
                hovertemplate=(
                    f"<b>{secondary_player.name}</b><br>"
                    "Score: %{x:.0f}<br>"
                    "Density: %{y:.4f}"
                    "<extra></extra>"
                ),
            )
        )

    if score_distribution_comparison.primary_normal_curve_points:
        primary_curve_scores = [
            point.score
            for point
            in score_distribution_comparison.primary_normal_curve_points
        ]

        primary_curve_densities = [
            point.density
            for point
            in score_distribution_comparison.primary_normal_curve_points
        ]

        figure.add_trace(
            go.Scatter(
                x=primary_curve_scores,
                y=primary_curve_densities,
                mode="lines",
                name=primary_player.name,
                showlegend=False,
                opacity=PRIMARY_LINE_OPACITY,
                line={
                    "color": PRIMARY_PLAYER_COLOR,
                    "width": PRIMARY_LINE_WIDTH,
                },
                hovertemplate=(
                    f"<b>{primary_player.name}</b><br>"
                    "Score: %{x:.0f}<br>"
                    "Density: %{y:.4f}"
                    "<extra></extra>"
                ),
            )
        )

    # Chart-specific layout remains here because score-bin ticks, density,
    # and overlapping bars are properties of this visualization.
    figure.update_layout(
        barmode="overlay",
        barcornerradius=BAR_CORNER_RADIUS,
        xaxis={
            "title": "Score",
            "tickmode": "array",
            "tickvals": bin_centers,
            "ticktext": bin_labels,
            "tickangle": 45,
            "fixedrange": True,
        },
        yaxis={
            "title": "Density",
            "rangemode": "tozero",
            "fixedrange": True,
        },
    )

    # Shared Wingspan chart styling is applied last so legend, margins,
    # hover presentation, and other common behavior remain centralized.
    apply_common_chart_layout(
        figure=figure,
    )

    return figure