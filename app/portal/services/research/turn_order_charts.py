
"""
Plotly visualizations for turn-order research.

Chart builders receive prepared descriptive statistics.
They perform no database queries or hypothesis testing.
"""

import plotly.graph_objects as go

from .turn_order_statistics import (
    StartingPositionAnalysisStatistics,
)


def _apply_starting_position_layout(
    *,
    figure: go.Figure,
    title: str,
    y_axis_title: str,
) -> None:
    """
    Apply consistent formatting to starting-position charts.
    """

    # 1. Configure the chart's appearance.
    figure.update_layout(
        title={
            "text": title,
            "x": 0.5,
            "xanchor": "center",
        },
        template="plotly_white",
        height=400,
        margin={
            "l": 60,
            "r": 30,
            "t": 80,
            "b": 60,
        },
        showlegend=False,
        hovermode="closest",
        dragmode=False,
    )

    # 2. Configure the categorical starting-position axis.
    figure.update_xaxes(
        title_text="Starting Position",
        type="category",
        categoryorder="array",
        categoryarray=["1", "2", "3", "4", "5"],
    )

    # 3. Configure the measurement axis.
    figure.update_yaxes(
        title_text=y_axis_title,
        zeroline=True,
        zerolinecolor="gray",
    )


def build_starting_position_win_rate_chart(
    *,
    statistics: StartingPositionAnalysisStatistics,
) -> go.Figure:
    """
    H1a: Visualize observed win rates by starting position.

    Ties count as non-wins, consistent with the research
    methodology and descriptive statistics.
    """

    # 1. Extract the five starting-position observations.
    positions = [
        statistics.positions[position]
        for position in range(1, 6)
    ]

    labels = [str(position.position) for position in positions]

    win_rates = [
        position.win_rate * 100
        if position.win_rate is not None
        else None
        for position in positions
    ]

    # 2. Prepare additional information for hover tooltips.
    hover_data = [
        [
            position.total_games,
            position.wins,
            position.losses,
            position.ties,
        ]
        for position in positions
    ]

    # 3. Construct the bar chart.
    figure = go.Figure()

    figure.add_trace(
        go.Bar(
            x=labels,
            y=win_rates,
            customdata=hover_data,
            marker_color="#4472C4",
            hovertemplate=(
                "Starting Position: %{x}<br>"
                "Win Rate: %{y:.2f}%<br>"
                "Games: %{customdata[0]}<br>"
                "Wins: %{customdata[1]}<br>"
                "Losses: %{customdata[2]}<br>"
                "Ties: %{customdata[3]}"
                "<extra></extra>"
            ),
        )
    )

    # 4. Apply common styling and percentage scale.
    _apply_starting_position_layout(
        figure=figure,
        title="H1a — Win Rate by Starting Position",
        y_axis_title="Win Rate (%)",
    )

    figure.update_yaxes(
        range=[0, 100],
        ticksuffix="%",
    )

    return figure


def build_starting_position_score_chart(
    *,
    statistics: StartingPositionAnalysisStatistics,
) -> go.Figure:
    """
    H1b: Visualize mean final scores by starting position.
    """

    # 1. Extract the five starting-position observations.
    positions = [
        statistics.positions[position]
        for position in range(1, 6)
    ]

    labels = [str(position.position) for position in positions]

    average_scores = [
        position.average_score
        for position in positions
    ]

    # 2. Prepare sample sizes for hover tooltips.
    game_counts = [
        position.total_games
        for position in positions
    ]

    # 3. Construct the bar chart.
    figure = go.Figure()

    figure.add_trace(
        go.Bar(
            x=labels,
            y=average_scores,
            customdata=game_counts,
            marker_color="#4472C4",
            hovertemplate=(
                "Starting Position: %{x}<br>"
                "Average Score: %{y:.2f}<br>"
                "Games: %{customdata}"
                "<extra></extra>"
            ),
        )
    )

    # 4. Apply common styling.
    _apply_starting_position_layout(
        figure=figure,
        title="H1b — Average Final Score by Starting Position",
        y_axis_title="Average Final Score",
    )

    # 5. Scale the Y-axis to the observed average scores.
    valid_scores = [
        score
        for score in average_scores
        if score is not None
    ]

    if valid_scores:
        minimum = min(valid_scores)
        maximum = max(valid_scores)

        # Provide padding around the observed range.
        score_range = maximum - minimum
        padding = max(score_range * 0.15, 2)

        figure.update_yaxes(
            range=[
                minimum - padding,
                maximum + padding,
            ],
        )

    return figure


def build_starting_position_score_differential_chart(
    *,
    statistics: StartingPositionAnalysisStatistics,
) -> go.Figure:
    """
    H1c: Visualize mean score differentials by position.

    Positive values favor the principal player.
    Negative values favor the opponent.
    """

    # 1. Extract the five starting-position observations.
    positions = [
        statistics.positions[position]
        for position in range(1, 6)
    ]

    labels = [str(position.position) for position in positions]

    average_differentials = [
        position.average_score_differential
        for position in positions
    ]

    # 2. Color bars according to the direction of the differential.
    colors = [
        "#B0B0B0" if value is None
        else "#4472C4" if value >= 0
        else "#D65A5A"
        for value in average_differentials
    ]

    game_counts = [
        position.total_games
        for position in positions
    ]

    # 3. Construct the diverging bar chart.
    figure = go.Figure()

    figure.add_trace(
        go.Bar(
            x=labels,
            y=average_differentials,
            customdata=game_counts,
            marker_color=colors,
            hovertemplate=(
                "Starting Position: %{x}<br>"
                "Average Differential: %{y:+.2f}<br>"
                "Games: %{customdata}"
                "<extra></extra>"
            ),
        )
    )

    # 4. Apply common styling.
    _apply_starting_position_layout(
        figure=figure,
        title="H1c — Average Score Differential by Position",
        y_axis_title="Average Score Differential",
    )

    # 5. Emphasize the zero-differential reference line.
    figure.update_yaxes(
        zeroline=True,
        zerolinewidth=2,
        zerolinecolor="#555555",
    )

    return figure
