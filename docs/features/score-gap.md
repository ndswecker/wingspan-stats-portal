# Game Score Gap - Feature Specification

## 1. Purpose

Add a **Game Score Gap** chart to the Player Score Trends page.

The chart compares the scores of the primary and secondary players in
games where both players participated. It shows the scoring gap for each
shared game while preserving the actual score range.

## 2. Scope

-   Available only when a secondary comparison player is selected.
-   Hidden during single-player analysis.
-   A game qualifies when both selected players have a `GameResult` for
    the same game.
-   Additional players may also have participated in the game.
-   Respect the applicable Trends date filters.
-   This feature is independent of Feathered Foe and does not use its
    exact-two-player restriction.

## 3. Data Service

Create a dedicated Game Score Gap data service.

For each qualifying game, return:

-   Game ID
-   Date played
-   Primary player score
-   Secondary player score
-   Low score
-   High score
-   Score gap
-   Winner or tie

Calculations:

``` text
low_score = min(primary_score, secondary_score)
high_score = max(primary_score, secondary_score)
score_gap = high_score - low_score
```

Order games chronologically from oldest to newest. Use game ID as the
secondary ordering key for multiple games on the same date.

The service owns data selection and calculations. It does not build
Plotly figures.

## 4. Chart Service

Create a dedicated Plotly Game Score Gap chart service.

Each qualifying game is represented by a vertical floating bar:

-   Bar base = low score
-   Bar height = score gap
-   Bar top = high score
-   The bar does not start at zero unless the low score is actually
    zero.

Bar color identifies the player with the higher score using the existing
player colors defined by `chart_style`:

-   Primary player higher score: `PRIMARY_PLAYER_COLOR`
-   Secondary player higher score: `SECONDARY_PLAYER_COLOR`
-   Tie: existing neutral chart color

Game Score Gap must reuse the shared chart styling and must not define
duplicate player colors locally.

X-axis labels use:

``` text
<Game ID> <M/D/YY>
```

Example:

``` text
445 7/10/26
```

Hover information includes:

-   Game ID and date
-   Primary player name and score
-   Secondary player name and score
-   Score gap
-   Winner or tie

Tied games must remain visibly represented even though their calculated
bar height is zero.

The chart service receives prepared data and performs no database
queries.

## 5. Game Navigation

Each chart bar must carry the corresponding game detail URL.

Clicking a bar navigates the browser to that game's detail page.

Navigation should use the application's existing game-detail route
rather than hard-coded URL paths.

## 6. Trends Integration

Integrate the feature into `player_score_trends`.

When a secondary player is selected:

1.  Select qualifying shared games.
2.  Build the Game Score Gap chart.
3.  Add the rendered chart to the template context.

When no secondary player is selected, do not select Game Score Gap data
or build the chart.

The template renders the chart only when comparison data is available.

## 7. Empty State

If a comparison is selected but no qualifying shared games exist for the
selected filters, display a concise empty state instead of an empty
chart.

Example:

> No shared games found for the selected players and date range.

## 8. Acceptance Criteria

The feature is complete when:

-   Single-player Trends does not display the Game Score Gap section.
-   Comparison mode includes games where both selected players
    participated.
-   Games with additional players are eligible.
-   Games containing only one selected player are excluded.
-   Date filtering is respected.
-   Bars begin at the lower actual score and end at the higher actual
    score.
-   X-axis labels contain game ID and date.
-   Multiple games on the same date remain individually identifiable.
-   Hover information identifies both scores and the gap.
-   Tied games remain visible.
-   Bar colors correctly identify the higher-scoring player and use the
    shared `chart_style` constants.
-   Clicking a bar opens the correct game detail page.
-   No qualifying games produces the defined empty state.
-   Data selection/calculation and Plotly rendering remain separate
    services.
