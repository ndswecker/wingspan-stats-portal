# Player Game History

## Purpose

Replace the existing `/games/` Game History page with a player-focused history of competitive game results.

Users can select a player to review their games chronologically. An optional second player can be selected to compare both players' independent results by date.

The existing `game_history` view and `game_history.html` template will be substantially rewritten.

---

## Game Rules

Only competitive (`MULTIPLE`) games are included. Solo games are excluded.

For each player participating in a competitive game:

* **Win** — the player has the unique highest score.
* **Tie** — the player shares the highest score.
* **Loss** — another player has a higher score.

There is no placement beyond Win/Loss/Tie.

The logic must support any valid number of competitive players.

---

## Player Game Result

Each game in a player's history should produce a structured result containing at minimum:

* Game
* Player
* Score
* Outcome (`WIN`, `LOSS`, or `TIE`)

The Game identity must be retained so the result can later link to a dedicated game-detail page.

Game-detail and game-editing functionality are not part of this feature.

---

## Daily Results

Player game results are grouped by `Game.date_played`.

Each player's daily result contains:

* Player
* Date
* Game results
* Games played
* Wins
* Losses
* Ties
* Total score

A date does not have an overall winner or result.

Daily average score is not required.

Dates should display newest first.

---

## Page Layout

Each date forms one visual row.

Within the row, the player's individual games are displayed horizontally as compact game cards.

Example:

```text
8/10/2026

Nate    [88 · LOSS] [106 · WIN] [101 · WIN]    2W · 1L · 0T · 295 pts
```

Each card represents one game and should be designed so it can later become a hyperlink to that game's detail page.

---

## Player Comparison

The page supports:

* One required primary player.
* One optional secondary player.

When two players are selected, their histories are calculated independently and aligned by date.

The primary player's lane appears above the secondary player's lane within each date.

```text
8/10/2026

Nate    [92 · LOSS] [108 · WIN] [101 · WIN]    2W · 1L · 0T · 301 pts
Nick    [97 · WIN]  [103 · WIN]                 2W · 0L · 0T · 200 pts
```

Comparison does **not** imply that the players competed against each other.

They may have:

* Played the same games.
* Played some games together.
* Played completely different games.

Game cards between player lanes are not positionally paired.

---

## Comparison Dates

In comparison mode, displayed dates are the union of both players' game dates.

If only one player played on a date, the other lane displays `No games`.

```text
8/6/2026

Nate    [110 · WIN] [104 · WIN]    2W · 0L · 0T · 214 pts
Nick    No games
```

---

## Date Filtering

The underlying services should support:

* Start date
* End date

The initial UI may expose predefined periods such as:

* Last 12 months
* Calendar year
* All time

Custom date ranges are not required initially.

---

## Service Responsibilities

Game-result and aggregation logic belongs in the service layer.

The implementation should provide clear responsibilities for:

### Game Selection

Retrieve a player's competitive games within the requested period with the related results required for outcome calculation.

### Game Outcome

Determine the selected player's Win/Loss/Tie result for an individual competitive game.

This should become the application's authoritative competitive-game outcome logic.

### Daily History

Group player game results by date and calculate:

* Games played
* Wins
* Losses
* Ties
* Total score

### Comparison Alignment

Align two independently calculated player histories using the union of their dates.

The exact service and function names may be determined during implementation.

---

## View Responsibilities

The rewritten view should primarily:

1. Validate player and period filters.
2. Request player history from services.
3. Request secondary-player history when applicable.
4. Align comparison results.
5. Build template context.
6. Render the page.

The view should not calculate game outcomes or daily statistics.

---

## Template Responsibilities

The rewritten template should:

* Render filters.
* Render dates.
* Render player lanes.
* Render game cards.
* Render daily totals.
* Render comparison results.
* Handle empty states.

Domain calculations should not occur in the template.

---

## Legacy Code

The existing Game History implementation was designed around two-player games and night winners.

Legacy logic may be removed or replaced, including:

* Two-player winner calculations.
* Night-winner calculations.
* Fixed two-player game rows.
* Existing Game History context-building logic.
* Legacy dashboard win/night-win calculations where appropriate.

Existing pages may expose dependencies on this logic during the refactor. Those dependencies can be migrated to the new shared services as necessary rather than preserving obsolete calculations.

---

## Edge Cases

The feature must support:

* Two-player games.
* Multiplayer games.
* Tied highest scores.
* Multiple games by one player on the same date.
* Different groups playing on the same date.
* Compared players playing together.
* Compared players playing separately.
* Compared players never playing each other.
* Different numbers of games per player per date.
* Dates where only one compared player played.
* Players or periods with no competitive games.
* Historical games belonging to inactive players.

---

## Out of Scope

This feature does not include:

* Solo games.
* Night or daily winners.
* Tournament results.
* Player rankings.
* Head-to-head statistics.
* Daily average scores.
* Game-detail pages.
* Game editing.
* Shared-game highlighting.
* Custom date ranges.

---

# Implementation Phases

## Phase 1 — Game Results

Implement and test the authoritative competitive Win/Loss/Tie calculation.

## Phase 2 — Player History

Select a player's competitive games and build daily results containing individual games and daily totals.

## Phase 3 — Comparison

Calculate two histories independently and align them by date.

## Phase 4 — Page Rewrite

Rewrite the existing `/games/` view and `game_history.html` using the new services.

## Phase 5 — Cleanup

Remove obsolete two-player and night-winner logic. Update other pages if legacy dependencies surface.

## Phase 6 — Testing

Verify game outcomes, multiplayer games, ties, daily aggregation, comparison alignment, empty states, and existing application functionality.

---

# Success Criteria

The feature is complete when:

* A player can view their competitive games grouped by date.
* Every game shows score and Win/Loss/Tie.
* Multiplayer games and ties are calculated correctly.
* Every date shows wins, losses, ties, games played, and total score.
* A second player's independent history can be aligned for comparison.
* Dates where only one player played remain visible.
* Solo games are excluded.
* Game identity is retained for future game-detail links.
* Calculations live in reusable services rather than the view or template.
* The `/games/` page no longer depends on the legacy two-player/night-winner model.
