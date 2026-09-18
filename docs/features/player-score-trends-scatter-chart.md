# Player Score Trends Date Filtering and Individual Game Score Chart

## Feature Summary

Enhance the existing Player Score Trends page in two related ways:

1.  Replace the existing period-based date selector with the
    application's standard optional Start Date / End Date filtering
    pattern.
2.  Add an individual-game scatter chart showing when games were played
    and the score recorded for each game.

The existing Player Score Trends page will continue to provide its
current monthly trend chart, score distribution chart, statistical
summary, and monthly summary. All existing and new analytical sections
must use the same selected players, game type, and date range.

## Goals

-   Let users inspect individual game scores across time.
-   Make periods of frequent play and inactivity visually apparent.
-   Support both single-player and two-player comparison views.
-   Align Player Score Trends date filtering with the date-selection
    behavior used elsewhere in the portal.
-   Ensure every Trends visualization and summary represents the same
    filtered set of games.
-   Reuse the existing game-result selection, friendship authorization,
    chart styling, and Plotly infrastructure.
-   Preserve the existing separation between data selection, statistical
    calculation, view orchestration, and chart presentation.

## Existing Trends Features

The Player Score Trends page currently provides:

-   Monthly average score trend chart.
-   Score distribution chart.
-   Statistical summary.
-   Monthly summary.
-   Primary player selection.
-   Optional comparison player selection.
-   Game type selection.
-   Period-based filtering.

This feature extends the existing page rather than introducing a new
page.

## Date Filter Changes

### Remove Period Selection

The existing `period` selector will be removed.

The page will no longer offer:

-   Last 12 Months.
-   Individual calendar years derived from the available dataset.

The existing period-resolution behavior, including
`resolve_score_trend_period()`, should no longer be required by the
Player Score Trends workflow once the new date filtering is implemented.

### New Date Controls

`PlayerScoreTrendsFilterForm` will provide:

-   **Player**
-   **Comparison Player** --- optional.
-   **Game Type**
-   **Start Date** --- optional.
-   **End Date** --- optional.

Standard HTML `date` inputs should be used.

### Date Actions

The form will provide:

-   **This Month** --- sets Start Date to the first day of the current
    month and End Date to the current date.
-   **All Time** --- clears Start Date and End Date.

These actions should follow the same interaction pattern used by the
Player Overview date filters.

### Date Range Behavior

Date filtering applies to `Game.date_played` and is inclusive.

-   No Start Date and no End Date: return all matching games.
-   Start Date only: return games on or after Start Date.
-   End Date only: return games on or before End Date.
-   Both dates: return games within the inclusive range.
-   Start Date after End Date: form validation error.

The selected or action-generated dates must repopulate the date fields
after submission.

## Shared Result Dataset

Player, optional Comparison Player, Game Type, Start Date, and End Date
define the datasets used by the entire Trends page.

The primary player's filtered `GameResult` queryset must drive:

-   Monthly average score calculations.
-   Score distribution calculations.
-   Statistical summary.
-   Monthly summary.
-   Individual Game Score scatter chart.

When a comparison player is selected, the comparison player's
corresponding filtered queryset must drive the same comparison-capable
features.

The individual sections must not independently select games using
different filtering rules.

The existing `select_game_results()` service should remain responsible
for selecting `GameResult` records by player, game type, and optional
inclusive start/end dates.

## Individual Game Score Chart

### Purpose

Add a Plotly chart that shows every individual game result across the
selected date range.

The chart is intended to answer two questions simultaneously:

-   When was the player playing?
-   What score did the player record in each game?

The spacing of points across the horizontal axis should also make
periods of frequent play and inactivity visible.

### Chart Type

The visualization will use discrete markers with no connecting lines.

Each marker represents exactly one `GameResult`.

The chart should not aggregate individual games into daily, weekly, or
monthly values.

### Axes

**X-axis: Date**

-   Uses `Game.date_played`.
-   Must use a true date/time axis so horizontal distance represents
    actual elapsed time.
-   Games separated by long periods of inactivity must retain the
    corresponding visual gap.

**Y-axis: Score**

-   Uses `GameResult.score`.
-   The axis should derive a useful range from the observed scores with
    reasonable visual padding.
-   The Y-axis should not be forced to start at zero when the observed
    score range makes that unnecessary.

### Single-Player Mode

When no Comparison Player is selected:

-   Display one marker series.
-   Every matching primary-player `GameResult` produces one point.
-   Use the existing shared Primary Player chart styling.

### Comparison Mode

When a Comparison Player is selected:

-   Display one marker series for the primary player.
-   Display one marker series for the comparison player.
-   Both series share the same date and score axes.
-   Use the existing shared Primary Player and Secondary Player chart
    colors/styles.
-   The legend should clearly identify each player.

The chart must not normalize, aggregate, or otherwise alter either
player's scores for comparison.

### Marker Presentation

Markers should be sized to remain readable when many games are present.

Some transparency should be used so overlapping or densely clustered
points remain as visually distinguishable as practical.

No artificial date jitter should be applied. A marker's horizontal
position must continue to represent the actual `Game.date_played` value.

Because `Game.date_played` stores a date rather than a time, multiple
results with the same date and score may occupy the exact same
coordinate. This is acceptable for the initial implementation.

### Hover Information

Hover information should provide useful identification for an individual
observation.

At minimum, hover should show:

-   Player.
-   Date played.
-   Score.

Game identity may also be included if useful during implementation.

The hover presentation should remain concise.

### Analytical Overlays

The scatter chart will not add:

-   Connecting lines.
-   Moving averages.
-   Regression or trend lines.
-   Normal curves.
-   Monthly averages.
-   Other statistical overlays.

Those analytical responsibilities remain with the existing Trends
features.

## Scatter Chart Service

Add a dedicated chart module:

`player_game_scatter_chart.py`

This module is responsible for constructing the Plotly scatter figure.

The chart builder should receive the already-filtered primary
`GameResult` queryset and, when applicable, the already-filtered
comparison-player queryset.

The chart builder may transform those supplied records into Plotly
presentation arrays such as:

-   X values.
-   Y values.
-   Hover/custom data.

It must not:

-   Perform database selection or filtering.
-   Independently determine authorization.
-   Perform statistical calculations.
-   Reimplement date filtering.

A separate `player_game_scatter.py` calculation service is not required
for the initial feature because each selected `GameResult` already maps
directly to one chart observation.

## Existing Service Responsibilities

The intended service boundaries are:

``` text
game_result_selection.py
    -> select filtered GameResult querysets

player_score_trends.py
    -> calculate monthly trend data

player_score_distribution.py
    -> calculate distribution and statistical data

player_score_trend_chart.py
    -> build existing Plotly trend visualizations

player_score_distribution_chart.py
    -> build existing Plotly distribution visualizations

player_game_scatter_chart.py
    -> build individual-game Plotly scatter visualization
```

The `player_score_trends` view remains responsible for orchestration.

## Monthly Trend Changes

The existing monthly trend functionality must support arbitrary optional
Start Date and End Date values rather than depending on a named period
such as `Last 12 Months` or a calendar year.

Monthly aggregation should continue to represent the complete selected
date range.

The monthly chart's labeling and X-axis presentation must no longer
depend on checks against a specific period label such as
`"Last 12 Months"`.

The implementation should choose month labels appropriate for arbitrary
ranges and avoid ambiguity when the selected range crosses calendar
years.

All Time may produce a long monthly series. This is acceptable; the
feature should not impose an artificial period restriction solely to
shorten the monthly chart.

## View Integration

The existing `player_score_trends` view will continue to:

1.  Validate the filter form.
2.  Determine the selected primary player and optional comparison
    player.
3.  Determine the selected game type.
4.  Resolve Start Date and End Date, including the This Month and All
    Time actions.
5.  Select the primary player's `GameResult` queryset.
6.  Select the comparison player's queryset when applicable.
7.  Pass those same datasets to the existing calculation services.
8.  Build the existing charts and summaries.
9.  Build the new individual-game scatter chart.
10. Render all results in the existing Player Score Trends template.

The scatter chart should use the existing Plotly JavaScript already
loaded for the page rather than loading another copy.

## Player Authorization

The existing Player Score Trends player-selection authorization must
remain unchanged.

A logged-in user may select only players already permitted by the
existing allowed-player/friendship infrastructure.

This feature will not introduce separate friendship or authorization
logic.

## Empty Results

A valid filter may return no primary-player games.

The page should retain a clear no-results state and should not render
misleading charts or statistical summaries.

Existing comparison behavior for a comparison player with no matching
results should be preserved or adjusted consistently across the page
during implementation.

The scatter chart must not independently invent a different no-results
policy.

## Responsive Presentation

The new chart must follow the existing Player Score Trends responsive
layout and shared chart styling.

The chart should remain usable on mobile devices.

Exact chart height, marker size, axis tick formatting, and Bootstrap
placement may be determined during implementation.

## Data Model

No database schema changes or migrations are expected.

The required scatter data already exists on:

-   `Game.date_played`.
-   `GameResult.score`.
-   `GameResult.player`.
-   The existing Game / GameResult relationship.

If implementation appears to require a model change, the design should
be reviewed before proceeding.

## Out of Scope

This feature will not add:

-   A new Trends page.
-   A new database model or migration.
-   A separate date range for the scatter chart.
-   Daily, weekly, or monthly aggregation of scatter points.
-   Artificial jitter of game dates.
-   Statistical overlays on the scatter chart.
-   New friendship rules.
-   New game-entry or confirmation behavior.
-   Game editing.
-   Changes to score-distribution mathematics.
-   A JavaScript date-range picker.

## Implementation Boundary

The intended high-level flow is:

``` text
Player Score Trends form
        |
        |-- Player
        |-- Comparison Player (optional)
        |-- Game Type
        |-- Start Date (optional)
        |-- End Date (optional)
        |
        v
select_game_results()
        |
        +--> monthly trend calculations
        |       -> monthly trend chart
        |
        +--> distribution/statistical calculations
        |       -> distribution chart + summaries
        |
        +--> individual GameResult records
                -> individual game scatter chart
```

The implementation should preserve the existing separation of concerns:

-   **Form:** input validation and allowed Player choices.
-   **Selection/service layer:** database filtering.
-   **Trend service:** monthly aggregation and comparison calculations.
-   **Distribution service:** statistical and distribution calculations.
-   **Chart services:** Plotly presentation only.
-   **View:** orchestration and date-action handling.
-   **Template:** responsive presentation.

## Completion Criteria

The feature is complete when:

-   The old Period selector is removed from Player Score Trends.
-   Start Date and End Date filters work with the documented inclusive
    behavior.
-   This Month correctly populates the first day of the current month
    through today.
-   All Time clears both date fields and returns all matching records.
-   Invalid reversed date ranges produce a form validation error.
-   All existing Trends calculations and visualizations use the selected
    date range.
-   The monthly trend works across arbitrary date ranges and across
    multiple calendar years.
-   The individual-game scatter chart renders every matching
    primary-player result.
-   Comparison mode renders matching results for both selected players.
-   Scatter points use actual game dates and individual scores.
-   Scatter points are not connected or artificially jittered.
-   Hover identifies the player, date, and score.
-   The scatter chart performs no independent database queries or
    statistical calculations.
-   Existing player/friend authorization remains intact.
-   Existing Trends features continue to function.
-   The page remains responsive and usable on mobile.
-   No database migration is required.
