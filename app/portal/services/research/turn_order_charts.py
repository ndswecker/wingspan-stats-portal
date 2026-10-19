
"""
Plotly visualizations for turn-order research.

Chart builders receive prepared descriptive statistics.
They perform no database queries or hypothesis testing.
"""

from datetime import date
from html import escape

import plotly.graph_objects as go

from .turn_order_statistics import (
    StartingPositionAnalysisStatistics,
    DirectPrecedingAnalysisStatistics,
    PlayerSpacingAnalysisStatistics,
)


def _apply_starting_position_layout(
    *,
    figure: go.Figure,
    title: str,
    y_axis_title: str,
    principal_player_name: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> None:
    """
    Apply consistent formatting to starting-position charts,
    including optional research context.
    """

    title_text = escape(title)

    if principal_player_name is not None:
        title_text += (
            f"<br><span style='font-size:13px;'>"
            f"Principal Player: {escape(principal_player_name)}"
            f"</span>"
        )

        date_label = (
            f"{start_date:%b %d, %Y}" if start_date else "Not available"
        )
        end_label = (
            f"{end_date:%b %d, %Y}" if end_date else "Not available"
        )

        title_text += (
            f"<br><span style='font-size:12px;color:gray;'>"
            f"Research Period: {date_label} – {end_label}"
            f"</span>"
        )

    figure.update_layout(
        title={
            "text": title_text,
            "x": 0.5,
            "xanchor": "center",
            "y": 0.96,
            "yanchor": "top",
        },
        template="plotly_white",
        height=460,
        margin={
            "l": 60,
            "r": 30,
            "t": 135,
            "b": 60,
        },
        showlegend=False,
        hovermode="closest",
        dragmode=False,
    )

    figure.update_xaxes(
        title_text="Starting Position",
        type="category",
        categoryorder="array",
        categoryarray=["1", "2", "3", "4", "5"],
    )

    figure.update_yaxes(
        title_text=y_axis_title,
        zeroline=True,
        zerolinecolor="gray",
    )


def build_starting_position_win_rate_chart(
    *,
    statistics: StartingPositionAnalysisStatistics,
    principal_player_name: str,
    start_date: date | None,
    end_date: date | None,
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
        principal_player_name=principal_player_name,
        start_date=start_date,
        end_date=end_date,
    )

    figure.update_yaxes(
        range=[0, 100],
        ticksuffix="%",
    )

    return figure


def build_starting_position_score_chart(
    *,
    statistics: StartingPositionAnalysisStatistics,
    principal_player_name: str,
    start_date: date | None,
    end_date: date | None
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
        principal_player_name=principal_player_name,
        start_date=start_date,
        end_date=end_date,
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
    principal_player_name: str,
    start_date: date | None,
    end_date: date | None,
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
        principal_player_name=principal_player_name,
        start_date=start_date,
        end_date=end_date,
    )

    # 5. Emphasize the zero-differential reference line.
    figure.update_yaxes(
        zeroline=True,
        zerolinewidth=2,
        zerolinecolor="#555555",
    )

    return figure

# Add DirectPrecedingAnalysisStatistics to the existing imports from
# .turn_order_statistics in turn_order_charts.py.


def _apply_direct_preceding_layout(
    *,
    figure: go.Figure,
    title: str,
    y_axis_title: str,
    principal_player_name: str,
    start_date: date | None,
    end_date: date | None,
) -> None:
    """Apply consistent formatting and research context to H2 charts."""

    title_text = escape(title)

    title_text += (
        f"<br><span style='font-size:13px;'>"
        f"Principal Player: {escape(principal_player_name)}"
        f"</span>"
    )

    start_label = (
        f"{start_date:%b %d, %Y}" if start_date else "Not available"
    )
    end_label = (
        f"{end_date:%b %d, %Y}" if end_date else "Not available"
    )

    title_text += (
        f"<br><span style='font-size:12px;color:gray;'>"
        f"Research Period: {start_label} – {end_label}"
        f"</span>"
    )

    figure.update_layout(
        title={
            "text": title_text,
            "x": 0.5,
            "xanchor": "center",
            "y": 0.96,
            "yanchor": "top",
        },
        template="plotly_white",
        height=460,
        margin={"l": 60, "r": 30, "t": 135, "b": 80},
        showlegend=False,
        hovermode="closest",
        dragmode=False,
    )

    figure.update_xaxes(
        title_text="Turn Order Relationship",
        type="category",
        categoryorder="array",
        categoryarray=["Directly Precedes", "Does Not Precede"],
    )

    figure.update_yaxes(
        title_text=y_axis_title,
        zeroline=True,
        zerolinecolor="#555555",
    )


def build_direct_preceding_win_rate_chart(
    *,
    statistics: DirectPrecedingAnalysisStatistics,
    principal_player_name: str,
    start_date: date | None,
    end_date: date | None,
) -> go.Figure:
    """H2a: Compare observed win rates (ties are non-wins)."""

    # 1. Prepare the two groups.
    groups = [statistics.directly_precedes, statistics.does_not_precede]
    labels = ["Directly Precedes", "Does Not Precede"]
    rates = [
        group.win_rate * 100 if group.win_rate is not None else None
        for group in groups
    ]
    hover_data = [
        [group.total_games, group.wins, group.losses, group.ties]
        for group in groups
    ]

    # 2. Build the comparison chart.
    figure = go.Figure()
    figure.add_trace(go.Bar(
        x=labels,
        y=rates,
        customdata=hover_data,
        marker_color=["#4472C4", "#8FAADC"],
        hovertemplate=(
            "%{x}<br>Win Rate: %{y:.2f}%<br>"
            "Games: %{customdata[0]}<br>Wins: %{customdata[1]}<br>"
            "Losses: %{customdata[2]}<br>Ties: %{customdata[3]}"
            "<extra></extra>"
        ),
    ))

    # 3. Apply consistent styling and the percentage scale.
    _apply_direct_preceding_layout(
        figure=figure,
        title="H2a — Win Rate by Direct-Preceding Status",
        y_axis_title="Win Rate (%)",
        principal_player_name=principal_player_name,
        start_date=start_date,
        end_date=end_date,
    )
    figure.update_yaxes(range=[0, 100], ticksuffix="%")
    return figure


def build_direct_preceding_score_chart(
    *,
    statistics: DirectPrecedingAnalysisStatistics,
    principal_player_name: str,
    start_date: date | None,
    end_date: date | None,
) -> go.Figure:
    """H2b: Compare mean final scores between the two groups."""

    # 1. Prepare scores and sample sizes.
    groups = [statistics.directly_precedes, statistics.does_not_precede]
    labels = ["Directly Precedes", "Does Not Precede"]
    scores = [group.average_score for group in groups]
    counts = [group.total_games for group in groups]

    # 2. Build the comparison chart.
    figure = go.Figure()
    figure.add_trace(go.Bar(
        x=labels,
        y=scores,
        customdata=counts,
        marker_color=["#4472C4", "#8FAADC"],
        hovertemplate=(
            "%{x}<br>Average Final Score: %{y:.2f}<br>"
            "Games: %{customdata}<extra></extra>"
        ),
    ))

    # 3. Apply styling and focus the scale on the observed means.
    _apply_direct_preceding_layout(
        figure=figure,
        title="H2b — Average Final Score by Direct-Preceding Status",
        y_axis_title="Average Final Score",
        principal_player_name=principal_player_name,
        start_date=start_date,
        end_date=end_date,
    )
    valid_scores = [score for score in scores if score is not None]
    if valid_scores:
        padding = max((max(valid_scores) - min(valid_scores)) * 0.15, 2)
        figure.update_yaxes(
            range=[min(valid_scores) - padding, max(valid_scores) + padding]
        )
    return figure


def build_direct_preceding_score_differential_chart(
    *,
    statistics: DirectPrecedingAnalysisStatistics,
    principal_player_name: str,
    start_date: date | None,
    end_date: date | None,
) -> go.Figure:
    """H2c: Compare mean score differentials (principal minus opponent)."""

    # 1. Prepare differentials and sample sizes.
    groups = [statistics.directly_precedes, statistics.does_not_precede]
    labels = ["Directly Precedes", "Does Not Precede"]
    differentials = [group.average_score_differential for group in groups]
    counts = [group.total_games for group in groups]

    # 2. Build the comparison chart.
    figure = go.Figure()
    figure.add_trace(go.Bar(
        x=labels,
        y=differentials,
        customdata=counts,
        marker_color=["#4472C4", "#8FAADC"],
        hovertemplate=(
            "%{x}<br>Average Score Differential: %{y:+.2f}<br>"
            "Games: %{customdata}<extra></extra>"
        ),
    ))

    # 3. Apply styling with a visible zero reference.
    _apply_direct_preceding_layout(
        figure=figure,
        title="H2c — Average Score Differential by Direct-Preceding Status",
        y_axis_title="Average Score Differential",
        principal_player_name=principal_player_name,
        start_date=start_date,
        end_date=end_date,
    )
    figure.update_yaxes(zeroline=True, zerolinewidth=2, zerolinecolor="#555555")
    return figure



def _apply_player_spacing_layout(
    *,
    figure: go.Figure,
    title: str,
    y_axis_title: str,
) -> None:
    """
    Apply consistent formatting to the four-category H3 charts.
    """

    # 1. Configure the chart appearance.
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
            "t": 85,
            "b": 65,
        },
        showlegend=False,
        hovermode="closest",
        dragmode=False,
    )

    # 2. Configure the categorical NPC spacing axis.
    figure.update_xaxes(
        title_text="Intervening NPCs",
        type="category",
        categoryorder="array",
        categoryarray=["0", "1", "2", "3"],
    )

    # 3. Configure the measurement axis.
    figure.update_yaxes(
        title_text=y_axis_title,
        zeroline=True,
        zerolinecolor="#555555",
    )


def build_player_spacing_win_rate_chart(
    *,
    statistics: PlayerSpacingAnalysisStatistics,
) -> go.Figure:
    """
    H3a: Visualize observed win rates by NPC spacing.

    Ties count as non-wins, consistent with the research
    methodology and descriptive statistics.
    """

    # 1. Extract the four NPC spacing groups.
    groups = [
        statistics.spacing_groups[spacing]
        for spacing in range(4)
    ]

    labels = [str(group.spacing) for group in groups]

    win_rates = [
        group.win_rate * 100
        if group.win_rate is not None
        else None
        for group in groups
    ]

    # 2. Prepare outcome counts for hover tooltips.
    hover_data = [
        [
            group.total_games,
            group.wins,
            group.losses,
            group.ties,
        ]
        for group in groups
    ]

    # 3. Construct the win-rate bar chart.
    figure = go.Figure()

    figure.add_trace(
        go.Bar(
            x=labels,
            y=win_rates,
            customdata=hover_data,
            marker_color="#4472C4",
            hovertemplate=(
                "Intervening NPCs: %{x}<br>"
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
    _apply_player_spacing_layout(
        figure=figure,
        title="H3a — Win Rate by NPC Spacing",
        y_axis_title="Win Rate (%)",
    )

    figure.update_yaxes(
        range=[0, 100],
        ticksuffix="%",
    )

    return figure


def build_player_spacing_score_chart(
    *,
    statistics: PlayerSpacingAnalysisStatistics,
) -> go.Figure:
    """
    H3b: Visualize mean final scores by NPC spacing.
    """

    # 1. Extract the four NPC spacing groups.
    groups = [
        statistics.spacing_groups[spacing]
        for spacing in range(4)
    ]

    labels = [str(group.spacing) for group in groups]

    average_scores = [
        group.average_score
        for group in groups
    ]

    # 2. Prepare sample sizes for hover tooltips.
    game_counts = [
        group.total_games
        for group in groups
    ]

    # 3. Construct the average-score bar chart.
    figure = go.Figure()

    figure.add_trace(
        go.Bar(
            x=labels,
            y=average_scores,
            customdata=game_counts,
            marker_color="#4472C4",
            hovertemplate=(
                "Intervening NPCs: %{x}<br>"
                "Average Final Score: %{y:.2f}<br>"
                "Games: %{customdata}"
                "<extra></extra>"
            ),
        )
    )

    # 4. Apply common styling.
    _apply_player_spacing_layout(
        figure=figure,
        title="H3b — Average Final Score by NPC Spacing",
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

        score_range = maximum - minimum
        padding = max(score_range * 0.15, 2)

        figure.update_yaxes(
            range=[
                minimum - padding,
                maximum + padding,
            ],
        )

    return figure


def build_player_spacing_score_differential_chart(
    *,
    statistics: PlayerSpacingAnalysisStatistics,
) -> go.Figure:
    """
    H3c: Visualize mean score differentials by NPC spacing.

    Positive values favor the principal player.
    Negative values favor the opponent.
    """

    # 1. Extract the four NPC spacing groups.
    groups = [
        statistics.spacing_groups[spacing]
        for spacing in range(4)
    ]

    labels = [str(group.spacing) for group in groups]

    average_differentials = [
        group.average_score_differential
        for group in groups
    ]

    # 2. Color bars according to differential direction.
    colors = [
        "#B0B0B0" if value is None
        else "#4472C4" if value >= 0
        else "#D65A5A"
        for value in average_differentials
    ]

    game_counts = [
        group.total_games
        for group in groups
    ]

    # 3. Construct the score-differential bar chart.
    figure = go.Figure()

    figure.add_trace(
        go.Bar(
            x=labels,
            y=average_differentials,
            customdata=game_counts,
            marker_color=colors,
            hovertemplate=(
                "Intervening NPCs: %{x}<br>"
                "Average Score Differential: %{y:+.2f}<br>"
                "Games: %{customdata}"
                "<extra></extra>"
            ),
        )
    )

    # 4. Apply common styling.
    _apply_player_spacing_layout(
        figure=figure,
        title="H3c — Average Score Differential by NPC Spacing",
        y_axis_title="Average Score Differential",
    )

    # 5. Emphasize the zero-differential reference line.
    figure.update_yaxes(
        zeroline=True,
        zerolinewidth=2,
        zerolinecolor="#555555",
    )

    return figure
