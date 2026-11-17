
# Achievement System — Feature Specification

**Project:** Wingspan Stats Portal  
**Status:** Draft — Iterative Design  
**Scope:** Event-Based Achievements  
**Last Updated:** November 16, 2026

---

## 1. Overview

The Achievement System awards players recognition for accomplishments derived from their recorded Wingspan game results.

Achievements are defined and governed by Python code. PostgreSQL stores records of achievements earned by players.

The system will eventually support multiple achievement categories, including:

- Event-based achievements
- Time-boxed achievements
- Potential future achievement types

This initial specification focuses exclusively on event-based achievements.

## 2. Architectural Principles

The Achievement System will operate as an integrated subsystem within the existing Django application.

Its architecture separates three responsibilities:

1. **Definition:** Python classes define achievements and their qualifying conditions.
2. **Evaluation:** Python services evaluate game results against achievement definitions.
3. **Persistence:** Django models store records of achievements earned by players.

The following principles apply:

- Achievement definitions and business logic reside in Python.
- PostgreSQL stores earned awards, not achievement definitions.
- Event-based achievements are evaluated when games are created or edited.
- Game-result confirmation is not required for achievement eligibility.
- Achievement evaluation is independent of Django views.
- Award creation and removal are automated.
- Players cannot manually accept, reject, hide, or remove awards.
- Event-based achievements do not require scheduled processing.

The system should remain modular enough to support other achievement types without substantially redesigning its core components.

## 3. Achievement Definition

An achievement represents a specific accomplishment that a player can earn.

Every achievement must define:

| Component | Responsibility |
|---|---|
| Code | Unique, stable identifier |
| Name | Human-readable achievement title |
| Description | Explanation of how the achievement is earned |
| Evaluation | Logic determining whether the achievement is earned |
| Award Policy | Rules governing whether and how often it can be earned |
| Persistence | Ability to associate the achievement with an awarded player |

Achievement definitions will be implemented as Python classes.

A common base class may provide shared attributes and behavior.

Specialized achievement classes will implement their own evaluation logic.

### 3.1 Event-Based Achievements

An event-based achievement evaluates an individual game and its associated player results.

Examples include:

- Scoring at least 180 points in a game.
- Winning a competitive game by at least 50 points.
- Reaching a specified score threshold in a solo game.

Event-based achievements may evaluate the entire game, including all associated `GameResult` records.

An achievement may award one or multiple qualifying players.

### 3.2 Repeatability

Some achievements may be earned multiple times.

For event-based achievements, repeatability is generally associated with distinct qualifying games.

A player must not receive duplicate instances of the same achievement for the same game result.

Specific repeatability policies will be defined by individual achievement classes.

## 4. Achievement Evaluation

Event-based achievements are evaluated automatically following successful game creation or modification.

Evaluation is performed against the current persisted state of the game.

The evaluator does not distinguish between newly created and previously existing games.

### 4.1 Evaluation Trigger

Achievement evaluation occurs after:

- A new game and its player results are saved.
- An existing game or its player results are modified.

Evaluation will be integrated into the existing game creation and update service layer.

Game-result confirmation does not trigger achievement evaluation.

### 4.2 Evaluation Process

The event-based achievement evaluator will:

1. Retrieve the game and its associated player results.
2. Identify applicable event-based achievement definitions.
3. Evaluate the game against those definitions.
4. Determine which players currently qualify for each achievement.
5. Retrieve existing event-based awards associated with the game.
6. Create awards that are newly earned.
7. Preserve awards that remain valid.
8. Delete awards that are no longer valid.

Evaluation and award reconciliation are performed together.

### 4.3 Evaluation Scope

Event-based evaluation is scoped to the game being processed.

Editing one game does not require evaluating every other game or player in the database.

The evaluator should operate efficiently by loading the relevant game and its associated results.

### 4.4 Idempotency

Achievement evaluation must be idempotent.

Repeated evaluation of an unchanged game must not:

- Create duplicate awards.
- Delete valid awards.
- Produce inconsistent database records.

Database uniqueness constraints should reinforce this behavior.

## 5. Award Persistence

Award records will be stored in a shared Django model, provisionally named `PlayerAchievement`.

The database represents achievements that players currently possess.

It is not intended to maintain a historical ledger of revoked achievements.

### 5.1 Proposed Model Fields

| Field | Purpose |
|---|---|
| `id` | Unique award record identifier |
| `player` | Player receiving the achievement |
| `achievement_code` | Identifier of the Python achievement definition |
| `source_result` | GameResult associated with the achievement |
| `awarded_at` | Timestamp when the award was recorded |

For event-based achievements, `source_result` establishes the relationship between an award and the game result that earned it.

The associated `Game` can be accessed through the `GameResult` relationship.

### 5.2 Referential Integrity

Event-based awards should be removed automatically when their source game result is deleted.

A cascading relationship between `PlayerAchievement` and `GameResult` is the preferred approach.

The model should prevent duplicate awards for the same achievement and source result.

The award's player must remain consistent with the player associated with its source result.

### 5.3 Future Extensibility

Future time-boxed achievements may not have a single source game result.

The persistence model should be designed with this possibility in mind.

Additional fields or source-identification mechanisms may be introduced when time-boxed achievements are specified.

A separate achievement-definition database table is not planned.

## 6. Award Reconciliation

Award reconciliation ensures that persisted event-based awards reflect the current state of the underlying game data.

Reconciliation occurs whenever a game is evaluated.

### 6.1 Award Creation

If a player qualifies for an achievement and no corresponding award exists, a new `PlayerAchievement` record is created.

### 6.2 Award Retention

If a player continues to qualify for an existing achievement, its award record remains unchanged.

### 6.3 Award Removal

If a player no longer qualifies for an existing achievement, the award record is deleted.

Removed awards are not retained as revoked or inactive records.

### 6.4 Game Result Corrections

Editing a score may cause awards to be created or removed.

For example:

1. Susan records a game with a score of 181.
2. The evaluator determines that she qualifies for an achievement requiring at least 180 points.
3. The system creates an award associated with Susan's game result.
4. Susan later corrects her score to 175.
5. The game is re-evaluated.
6. The previously issued award is deleted.

If Susan instead changes the score from 175 to 181, the evaluator creates the newly qualifying award.

### 6.5 Player Assignment Changes

If an existing game result is reassigned to a different player, reconciliation must ensure that awards are assigned to the correct player.

An award must not remain associated with a previous player after the source result has been reassigned.

### 6.6 Deleted Games and Results

Deleting a game result removes its associated event-based awards.

Deleting a game removes its associated game results and, consequently, their event-based awards.

## 7. Achievement Services

Achievement functionality will reside in a dedicated Python package within the Django application.

A potential organization is:

```text
portal/
    services/
        achievements/
            base.py
            event_achievements.py
            event_evaluator.py
```

This structure is preliminary.

### 7.1 Base Achievement

The base achievement class will provide common identity and metadata conventions.

It may also define a shared interface for specialized achievement types.

### 7.2 Event Achievement Classes

Individual event achievement classes will implement qualifying rules.

Achievement classes should remain focused on evaluating eligibility rather than directly managing database records.

The event evaluation interface should support examining an entire game and returning qualifying player results.

### 7.3 Event Evaluator

The event evaluator coordinates:

- Loading the relevant game data.
- Executing registered achievement definitions.
- Identifying qualifying awards.
- Comparing eligible awards with existing records.
- Persisting additions and deletions.

A conceptual entry point is:

```python
evaluate_game_achievements(game)
```

A separate generalized awarding service is not required for the initial implementation.

Shared persistence helpers may be introduced if useful.

## 8. Integration with Game Management

The evaluator will integrate with the existing game-management service layer.

The expected integration points are:

- `create_game()`
- `update_game()`

Achievement evaluation should operate only on successfully saved game data.

Database transactions should prevent partial game updates from producing inconsistent award records.

The precise integration mechanism will be determined after reviewing the existing `game_entry.py` service.

## 9. Player Experience

Players will be able to view achievements they have earned.

The initial implementation should support retrieving a player's awards from the database.

Potential display locations include:

- Account page
- Player Overview
- Future player profile or achievement gallery

Award presentation will be designed separately.

Players cannot manually modify their awarded achievements.

Correcting the underlying game data is the mechanism for changing an event-based award's eligibility.

## 10. Time-Boxed Achievements — Future Scope

Time-boxed achievements are explicitly outside the initial implementation scope.

They will use separate Python evaluation classes and execution triggers.

Examples include:

- Most competitive games played during a calendar month.
- Highest solo score during a calendar month.
- Other achievements based on a defined date range.

Unlike event-based achievements, time-boxed achievements will be evaluated when their designated periods have completed.

A scheduled evaluation process will be designed separately.

Both achievement types should ultimately be able to use a common award persistence model where appropriate.

## 11. Open Design Questions

The following decisions remain unresolved:

1. Exact base achievement class design and evaluation interface.
2. Achievement registration and discovery mechanism.
3. Detailed `PlayerAchievement` model constraints.
4. How award policies govern non-repeatable event achievements.
5. Transaction boundaries between game updates and award reconciliation.
6. Precise handling of deleted or reassigned game results during evaluation.
7. Award metadata required for future presentation.
8. Persistence requirements for future time-boxed achievements.
9. Whether and how existing historical games should be evaluated retroactively.

These questions will be addressed iteratively during feature development.

## 12. Initial Implementation Scope

The first implementation should demonstrate the complete event-based achievement lifecycle.

The initial milestone will include:

- A Python achievement definition.
- An event-based evaluator.
- A persisted `PlayerAchievement` model.
- Automatic evaluation after game creation and editing.
- Award creation and deletion through reconciliation.
- Duplicate prevention.
- Tests covering award creation, retention, removal, and repeated evaluation.

A simple score-threshold achievement is recommended as the first implementation.

Scheduling, time-boxed achievements, notifications, and advanced award presentation are excluded from the initial milestone.

---

## 13. Current Design Summary

The Achievement System is a modular Django subsystem responsible for evaluating and persisting player accomplishments.

Event-based achievements are implemented as Python classes and evaluated whenever relevant game data is created or modified.

The evaluator determines which awards should currently exist for the game and synchronizes the database accordingly.

Awards are automatically created when earned and deleted when no longer valid.

The database stores current awarded achievements, while Python remains the authoritative source for achievement definitions, qualifying rules, and evaluation behavior.

This document establishes the initial event-based achievement architecture and will evolve as implementation decisions are finalized.
