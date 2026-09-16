# Player Overview Game History

## Feature Summary

Enhance the existing Player Overview so an authenticated user can select a player, game type, and optional date range and see both:

- General statistics for the selected games.
- A chronological history of the individual games that produced those statistics.

The feature is intended for straightforward performance review and game navigation. It does not replace or duplicate the analytical purpose of Competitive History.

## Goals

- Let users review their own performance or a current friend's performance over a selected timeframe.
- Ensure General Statistics and Game History always represent the same filtered set of games.
- Provide direct navigation from each history row to the existing Game Detail page.
- Keep the interface compact and usable on mobile phones.
- Reuse existing Player Overview authorization, models, services, and date-filtering patterns where appropriate.

## Filter Controls

The existing Player Overview result-selection form will be extended to include:

- **Player**
- **Game Type**
- **Start Date**
- **End Date**

The Player and Game Type remain required. Start Date and End Date are optional.

The form will also provide the existing-style date actions:

- **This Month** — selects games from the first day of the current month through the current date.
- **All Time** — clears the date restriction.

Standard HTML `date` inputs should be used. A custom JavaScript date-range picker is not required.

## Player Authorization

The Player selector will continue to use the existing allowed-player infrastructure.

A logged-in user may select only:

- Their own Player.
- Players currently permitted through the existing friendship rules.

This feature will not introduce or duplicate friendship authorization logic.

## Date Range Behavior

Date filtering applies to `Game.date_played` and is inclusive.

- No Start Date and no End Date: return all matching games.
- Start Date only: return games on or after the Start Date.
- End Date only: return games on or before the End Date.
- Both dates: return games within the inclusive range.
- Start Date after End Date: form validation error.

## Shared Result Dataset

Player, Game Type, Start Date, and End Date collectively define one filtered `GameResult` dataset.

That same complete dataset must drive both:

1. General Statistics.
2. Game History.

The two sections must not independently select or filter games.

The existing general-statistics calculation should remain responsible only for calculating statistics from the supplied results. Date filtering and other selection concerns belong in the result-selection layer.

## General Statistics

The existing General Statistics section will continue to display statistics such as:

- Games Played
- Average Score
- Lowest Score
- Highest Score

These values must be calculated from the complete filtered dataset.

No new statistical calculations are required by this feature.

## Game History

A Game History section will be added below General Statistics.

Each matching `GameResult` will produce one row.

The table will contain only:

| Column | Purpose |
| --- | --- |
| Date | Date the game was played and hyperlink to the existing Game Detail page |
| Type | Solo or Competitive game type |
| Score | Selected player's score |
| Status | Confirmation status of the selected player's `GameResult` |

The Status value represents the selected player's `GameResult.is_confirmed`. It is not an aggregate game-level confirmation state.

### Ordering

Games will be displayed newest first.

Ordering must be deterministic when multiple games occurred on the same date. The intended ordering is:

1. `date_played` descending.
2. Game ID descending.

## Mobile Presentation

Mobile usability is a primary requirement.

The history table must avoid unnecessary horizontal width.

In particular:

- There will be no dedicated **View Game** column.
- The Date value itself will link to Game Detail.
- Game-type labels may use concise presentation labels such as `Solo` and `Competitive`.
- The implementation should avoid adding secondary information such as opponents, turn order, outcomes, or player counts.

Exact Bootstrap layout and date formatting may be determined during implementation.

## Empty Results

A valid filter may return no games.

The page should provide a clear no-results state and must not present misleading General Statistics when the filtered dataset is empty.

Exact wording and presentation may be determined during implementation.

## Pagination

Game History will **not** be paginated in this feature.

All games matching the selected filters will be displayed, newest first. The expected dataset is currently on the order of hundreds of lightweight rows, and the date filters provide the primary mechanism for narrowing the history.

If pagination is introduced later, it must paginate only the Game History presentation. General Statistics must continue to be calculated from the complete filtered dataset.

## Existing Infrastructure to Reuse

The feature should reuse the existing:

- Player Overview authentication boundary.
- Allowed-player selection logic.
- `PlayerStatisticsFilterForm`.
- Game-result selection service where appropriate.
- General-statistics calculation service.
- `Game`, `GameResult`, and `Player` models.
- Game Detail route.
- Bootstrap styling and responsive layout patterns.

## Data Model

No database schema changes or migrations are expected.

The required information already exists on `Game` and `GameResult`.

If implementation appears to require a model change, the design should be reviewed before proceeding.

## Out of Scope

This feature will not add:

- Pagination.
- Opponent names.
- Player counts.
- Turn order.
- Win/Loss/Tie outcomes.
- Comparative analysis.
- New confirmation behavior.
- Game editing.
- New friendship or authorization rules.
- New statistical calculations.
- A JavaScript date-range library.

Competitive History remains the application feature for deeper analytical and comparative game-history views.

## Implementation Boundary

The intended high-level flow is:

`Player Overview form -> filtered GameResult dataset -> General Statistics + Game History`

The implementation should preserve the existing separation of concerns:

- **Form:** input validation and allowed Player choices.
- **Selection/service layer:** database filtering and deterministic ordering.
- **Statistics service:** calculations over supplied results.
- **View:** orchestration.
- **Template:** responsive presentation and Game Detail links.
