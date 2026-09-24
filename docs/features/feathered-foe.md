# Feathered Foe --- Feature Requirements

## 1. Feature Summary

Feathered Foe is a dedicated two-player competitive history view for
players who regularly play head-to-head games.

The feature intentionally presents results as a dense, spreadsheet-like
rivalry ledger. It is not intended to replace Competitive History or
become a general analytics page.

A user selects two players and an optional date range. The feature then
displays only competitive games in which those two players, and no other
players, participated.

The page provides:

-   a current rivalry leader based on game wins;
-   spreadsheet-style aggregate totals for each player;
-   individual game results;
-   per-day ("night") results;
-   links back to the underlying Game Detail pages.

Turn order is included in the service output for future use but is not
displayed in the initial version.

------------------------------------------------------------------------

## 2. Navigation

Feathered Foe does not receive a top-level navigation entry.

The Competitive History page provides a secondary link to the Feathered
Foe page.

Feathered Foe has its own URL, view, form, service, and template.

------------------------------------------------------------------------

## 3. Filters

The page provides:

-   Primary Player
-   Secondary Player
-   Start Date
-   End Date
-   Submit
-   This Month
-   All Time

Both player selectors use the application's normal allowed-player rules.

The same player cannot be selected as both Primary Player and Secondary
Player.

### Date Behavior

Date behavior matches the existing Player Overview date-range behavior.

-   Start and end dates are inclusive.
-   Blank Start Date means no lower date boundary.
-   Blank End Date means no upper date boundary.
-   This Month sets Start Date to the first day of the current month and
    End Date to the current date.
-   All Time clears both date fields.

------------------------------------------------------------------------

## 4. Qualifying Games

A game qualifies for Feathered Foe only when all of the following are
true:

1.  The game is competitive.
2.  The Primary Player participated.
3.  The Secondary Player participated.
4.  No other human player participated.
5.  The game's date falls within the selected date range, when date
    boundaries are supplied.

The participant set for every qualifying game must therefore be exactly:

``` text
{Primary Player, Secondary Player}
```

A multiplayer game containing both selected players plus one or more
additional players does not qualify.

Examples:

``` text
Nick + Nate                 QUALIFIES
Nick + Nate + Josh          DOES NOT QUALIFY
Nick + Nate + Josh + Ed     DOES NOT QUALIFY
Nick + Josh                 DOES NOT QUALIFY
Nate + Josh                 DOES NOT QUALIFY
```

------------------------------------------------------------------------

## 5. Ordering

Results are displayed newest first.

Nights are ordered by `date_played` descending.

Games occurring on the same date use a deterministic secondary ordering,
with the newest/highest Game ID first.

------------------------------------------------------------------------

## 6. Game Result Rules

Each qualifying game contains exactly two player results.

For each game:

-   the player with the higher score is the game winner;
-   equal scores produce a game tie.

A tied game gives neither player a game win or game loss.

Each displayed game provides a link to its existing Game Detail page
using the Game ID.

------------------------------------------------------------------------

## 7. Night Definition

A "night" consists of all qualifying Feathered Foe games played on the
same `date_played` value.

A night functions as a small tournament between the selected players.

Games played by either player against other opponents on the same date
have no effect on the Feathered Foe night.

### Night Winner

The night winner is determined in this order:

1.  Compare the number of game wins earned by each player during the
    night.
2.  If game wins are unequal, the player with more game wins wins the
    night.
3.  If game wins are equal, compare the sum of each player's scores
    across all games that night.
4.  The player with the higher nightly score total wins the night.
5.  If both game wins and nightly score totals are equal, the night is a
    tie.

A tied individual game contributes its score to each player's nightly
score total but contributes no game win or loss.

Night wins are supplemental rivalry information and do not determine the
overall current winner.

------------------------------------------------------------------------

## 8. Current Winner

The page prominently displays the current winner at the top.

The current winner is determined by total game wins within the currently selected dataset.

- If Primary Player has more game wins, Primary Player is the current winner.
- If Secondary Player has more game wins, Secondary Player is the current winner.
- If both players have the same number of game wins, total score is used as the tiebreaker.
- If Primary Player has the higher total score, Primary Player is the current winner.
- If Secondary Player has the higher total score, Secondary Player is the current winner.
- If both players have the same number of game wins and the same total score, the rivalry is currently tied.

Night wins are not used to determine the current winner.

------------------------------------------------------------------------

## 9. Aggregate Metadata

Spreadsheet-style aggregate metadata is displayed near the top of the
page for easy access.

For each player, display:

-   Score Total
-   Game Wins
-   Game Losses
-   Night Wins
-   Night Losses

The metadata represents only games contained in the currently selected
Feathered Foe dataset.

The presentation should resemble column totals in a spreadsheet rather
than a separate analytics dashboard.

Game and night ties are not credited as wins or losses to either player.

------------------------------------------------------------------------

## 10. Game Ledger

Below the current-winner and aggregate sections, the page displays the
rivalry history as a dense spreadsheet-style table.

The table should prioritize compactness and rapid scanning rather than
large cards or generous row spacing.

Conceptually:

  ------------------------------------------------------------------------
  Date / Game    Primary Player Secondary Player Game Win     Night Win
  ------------ ---------------- ---------------- ------------ ------------
  9/20/26 ---               116              139 Secondary    Secondary
  Game 150                                                    

  9/20/26 ---               128              123 Primary      
  Game 149                                                    

  9/19/26 ---               101              118 Secondary    Secondary
  Game 148                                                    
  ------------------------------------------------------------------------

Actual player names should be used as score-column headings.

The Game ID or associated row element links to the existing Game Detail
view.

The Night Win value should be presented once for the date group rather
than redundantly on every game row.

The exact visual treatment may be refined during template
implementation, but the spreadsheet-like density is a feature
requirement.

------------------------------------------------------------------------

## 11. Service Responsibilities

Feathered Foe uses a dedicated service responsible for the complete
rivalry dataset.

The service accepts:

``` text
primary_player
secondary_player
start_date (optional)
end_date (optional)
```

The service is responsible for:

-   selecting qualifying games;
-   enforcing the exact two-player matchup constraint;
-   ordering the selected games;
-   constructing individual game result objects;
-   determining each game winner;
-   grouping games by date;
-   determining each night winner;
-   calculating per-player aggregate metadata;
-   determining the current winner;
-   returning a structured, presentation-ready result.

The view should not perform matchup selection, winner calculations,
night calculations, or aggregate calculations.

The template should not contain business logic for determining winners.

------------------------------------------------------------------------

## 12. Service Return Structure

The service return value should mirror the domain hierarchy rather than
returning a flat collection of template-specific values.

Conceptually:

``` text
FeatheredFoe
│
├── primary_player
├── secondary_player
├── primary_summary
├── secondary_summary
├── current_winner
│
└── nights[]
    │
    ├── date_played
    ├── winner
    │
    └── games[]
        │
        ├── game_id
        ├── winner
        │
        └── results[]
            ├── player
            ├── score
            └── turn_order
```

Explicit typed objects/dataclasses are preferred over loosely structured
dictionaries.

A representative structure is:

``` python
@dataclass(frozen=True)
class FeatheredFoeGameResult:
    player: Player
    score: int
    turn_order: int | None


@dataclass(frozen=True)
class FeatheredFoeGame:
    game_id: int
    winner: Player | None
    results: list[FeatheredFoeGameResult]


@dataclass(frozen=True)
class FeatheredFoeNight:
    date_played: date
    winner: Player | None
    games: list[FeatheredFoeGame]


@dataclass(frozen=True)
class FeatheredFoePlayerSummary:
    player: Player
    score_total: int
    game_wins: int
    game_losses: int
    night_wins: int
    night_losses: int


@dataclass(frozen=True)
class FeatheredFoe:
    primary_player: Player
    secondary_player: Player
    primary_summary: FeatheredFoePlayerSummary
    secondary_summary: FeatheredFoePlayerSummary
    current_winner: Player | None
    nights: list[FeatheredFoeNight]
```

Exact class and field names may be refined during implementation, but
the nested hierarchy is part of the feature design.

`winner = None` represents a tie at the applicable level.

------------------------------------------------------------------------

## 13. Turn Order

Turn order is not displayed in the initial Feathered Foe UI.

However, each game result returned by the service includes the existing
`turn_order` value.

This deliberately preserves the data in the service contract so a later
version can display or analyze turn order without restructuring the
primary result hierarchy.

No new turn-order calculations are required for this version.

------------------------------------------------------------------------

## 14. Authorization

Both selected players must come from the players the acting user is
permitted to view under the application's existing player/friendship
rules.

The feature must not provide a mechanism for accessing another player's
results outside those existing authorization rules.

------------------------------------------------------------------------

## 15. Data Model

No database changes are required for the initial version.

Feathered Foe derives its results from existing game and game-result
data, including:

-   game date;
-   human-player mode;
-   participating players;
-   score;
-   turn order.

Game winners, night winners, aggregate rivalry metadata, and the current
winner are calculated values and are not persisted.

This avoids duplicated state becoming stale when an existing game is
edited.

------------------------------------------------------------------------

## 16. Implementation Boundaries

### Form

Responsible for:

-   player choices;
-   date input;
-   preventing the same player from being selected twice;
-   date-range validation;
-   existing allowed-player authorization behavior.

### Service

Responsible for:

-   database selection;
-   exact participant-set filtering;
-   deterministic ordering;
-   game result construction;
-   game winner calculation;
-   night grouping;
-   night winner calculation;
-   aggregate metadata;
-   current-winner calculation;
-   structured return objects.

### View

Responsible for:

-   authentication;
-   form binding;
-   This Month / All Time actions;
-   calling the Feathered Foe service after valid submission;
-   passing the form and service result to the template.

### Template

Responsible for:

-   current-winner presentation;
-   spreadsheet-style aggregate metadata;
-   dense game/night ledger;
-   Game Detail links;
-   empty-state presentation;
-   responsive presentation.

The template should not calculate domain outcomes.

------------------------------------------------------------------------

## 17. Empty State

When the selected players have no qualifying games in the selected date
range, the page should clearly state that no head-to-head games were
found.

The page should continue to display the filter controls so another
player pair or date range can be selected.

No winner should be declared when the dataset contains no qualifying
games.

------------------------------------------------------------------------

## 18. Out of Scope for Initial Version

The initial Feathered Foe feature does not include:

-   top-level navigation;
-   general multiplayer comparisons;
-   games containing players other than the selected pair;
-   charts or trend analysis;
-   average-score analytics;
-   turn-order display;
-   turn-order win-rate analysis;
-   persisted winner fields;
-   editing games from the Feathered Foe page;
-   changing existing game-confirmation workflows.

These may be considered independently in later versions.
