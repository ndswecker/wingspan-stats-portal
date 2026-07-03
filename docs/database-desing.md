# Database Design

This document describes the database schema for the Wingspan Stats Portal. It serves as the working specification for the application's data model and business rules.

---

# Player

Represents a person whose Wingspan results are tracked.

## Fields

| Field | Description |
|---|---|
| `id` | System-generated unique identifier. |
| `name` | Required player name. Must be unique. Maximum length: 50 characters. |
| `is_active` | Indicates whether the player is available for new game entry. Defaults to `true`. Inactive players remain in historical records. |

## Default Ordering

Players are ordered alphabetically by `name`.

---

# Game

Represents one completed Wingspan game.

## Fields

| Field | Description |
|---|---|
| `id` | System-generated unique identifier. |
| `date_played` | Required calendar date when the game was played. |

## Default Ordering

Games are ordered by:

1. `date_played` newest first
2. `id` newest first when multiple games share the same date

---

# GameResult

Represents one player's result within one game.

## Fields

| Field | Description |
|---|---|
| `id` | System-generated unique identifier. |
| `game` | Required reference to the game this result belongs to. |
| `player` | Required reference to the player this result belongs to. |
| `turn_order` | Optional numeric turn position for this player within the game. Historical records may leave this blank. |
| `score` | Required final score earned by the player. |

## Constraints

The following rules are enforced by the database:

- A player may only appear once within a single game.
- A known turn order value may only be assigned once within a single game.
- Unknown turn order values may be left blank.

## Delete Behavior

- Deleting a game deletes its related `GameResult` records.
- Deleting a player is blocked if that player appears in historical game results.

## Default Ordering

Game results are ordered by:

1. `game`
2. `score` highest first
3. `player`

---

# Business Rules

## Winner Determination

The database does not store a manually selected winner.

The winner is derived from `GameResult.score`:

- The player with the highest score is the winner.
- If multiple players share the highest score, the game is treated as a tie.

This preserves historical data accurately and avoids storing manually interpreted outcomes.

## Turn Order

Turn order is stored as raw optional data.

Derived statistics, such as whether one player immediately preceded another player, are calculated during statistical analysis rather than stored directly in the database.