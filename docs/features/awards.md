# Achievement System — Feature Specification

**Project:** Wingspan Stats Portal  
**Status:** Draft — Iterative Design  
**Current implementation scope:** Event-based achievements  
**Updated:** November 17, 2026

---

## 1. Purpose and Scope

The Achievement System recognizes player accomplishments calculated from recorded Wingspan games. An **achievement** (also called an **award**) is a defined accomplishment; an **earned award** is an association between a player and that accomplishment, optionally tied to a particular game result.

The system will eventually support event-based and time-boxed achievements. **Only event-based achievements are in scope for the first implementation.** Time-boxed achievements will have their own evaluation classes and scheduled triggers, but may share the same relational award catalog and recipient records.

## 2. Architectural Decisions

The system is part of the existing Django application—not an independent microservice or worker.

Its responsibilities are separated into:

1. **Definition:** Python achievement classes own stable identifiers, metadata, and qualifying rules.
2. **Evaluation:** An event-based evaluator checks a game against registered rules and reconciles the awards that should exist.
3. **Persistence:** Django models/PostgreSQL maintain a normalized achievement catalog and the awards earned by players.

Agreed operating rules:

- Python is authoritative for achievement definitions and eligibility logic; the database does not evaluate conditions.
- An `Achievement` table catalogs unique achievement types; a `PlayerAchievement` table links those types to recipients and evidence.
- Event-based achievements run when a game is successfully created or edited, **not** when player results are confirmed.
- Awards require no player acceptance and cannot be hidden, dismissed, or manually removed by players.
- If an edited game ceases to qualify for an award, the evaluator **deletes** the corresponding `PlayerAchievement` row. There is no active/revoked status or revocation ledger in this iteration.
- Event-based evaluation and reconciliation are scoped to the **changed game**, not all games or players.
- A rerun against unchanged data must not create duplicate awards or change valid records.
- No overnight scheduler is needed for event-based achievements.

## 3. Domain Concepts

### 3.1 Python achievement definition

An achievement class defines:

| Component | Responsibility |
|---|---|
| `code` | Unique, stable programmatic identity, e.g. `the_180_club` |
| `name` | Human-readable title, e.g. `The 180 Club` |
| `description` | Plain-language qualification description |
| Evaluation rule | Python logic that determines which result(s) qualify |
| Award policy | Whether/how the achievement may repeat |
| Registration behavior | A way to ensure its catalog record exists and metadata is synchronized |

An event-based class may inspect the **whole game** and all its results, even when the award is ultimately associated with one player's result. This supports both score thresholds and comparative achievements such as winning by at least 50 points.

### 3.2 Achievement catalog record

A row in `Achievement` describes **one unique achievement type**. It is not evidence that a particular player earned anything. Many `PlayerAchievement` rows can refer to the same catalog entry.

### 3.3 Player award record

A row in `PlayerAchievement` represents an **actual earned award**. For an event-based achievement it identifies the recipient, catalog achievement, and source `GameResult`.

The award exists while the result qualifies. The evaluator creates or deletes the row as game data changes.

## 4. Database Design

Two normalized Django models are planned.

### 4.1 `Achievement`

| Field | Type / relationship | Purpose |
|---|---|---|
| `id` | Primary key | Database identity |
| `code` | `CharField`, unique | Stable link to the Python class/registry |
| `name` | `CharField` | Display title |
| `description` | `TextField` | Display explanation |

**One catalog row per achievement code**, regardless of how many times it has been awarded. Descriptive metadata is stored once rather than copied into every earned award.

Changes to a catalog name or description affect the display of all linked awards. Historical wording snapshots are **not** required in the current design.

### 4.2 `PlayerAchievement`

| Field | Type / relationship | Purpose |
|---|---|---|
| `id` | Primary key | Award-instance identity |
| `player` | FK to `Player` | Recipient |
| `achievement` | FK to `Achievement` | Type of award earned |
| `source_result` | FK to `GameResult`, nullable | Evidence for an event-based award |
| `awarded_at` | Timestamp | When the earned-award row was created |

**Proposed deletion policies:**

- `source_result`: `on_delete=CASCADE`, so deleting a result (or its game) removes source-linked awards.
- `achievement`: `on_delete=PROTECT`, so deleting a catalog entry cannot silently erase earned awards.
- `player`: `on_delete=CASCADE` is the current candidate, consistent with a player-owned earned-award row; confirm before migration if player deletion policy changes.

For event-based awards, `source_result` is **required by the application**, though it may be nullable at the schema level to leave room for future time-boxed awards.

### 4.3 Uniqueness and repeatability

For a repeatable event-based achievement, enforce uniqueness of the combination:

`(achievement, source_result)`

Each `GameResult` belongs to one player, so this prevents the same result from earning the same achievement twice. It **does not** prevent multiple players from earning that achievement, or one player from earning it from multiple different results.

The evaluator must ensure `PlayerAchievement.player` matches `source_result.player`. That cross-table consistency is not guaranteed by the proposed unique constraint alone.

**Open:** How to represent *one-time-per-player* achievements and the exact uniqueness rules for non-event awards. Note that PostgreSQL's normal unique constraint permits multiple `NULL` values for `source_result`; future time-boxed awards will require their own identity/uniqueness strategy.

## 5. Python Definitions and Catalog Registration

The code for an achievement is authoritative; its database catalog record is a synchronized representation.

An illustrative class interface:

```python
class BaseAchievement:
    code: str
    name: str
    description: str

    @classmethod
    def register(cls):
        achievement, created = Achievement.objects.update_or_create(
            code=cls.code,
            defaults={
                "name": cls.name,
                "description": cls.description,
            },
        )
        return achievement


class The180Club(BaseAchievement):
    code = "the_180_club"
    name = "The 180 Club"
    description = "Score at least 180 points in a game."
```

**This is a design sketch, not final implementation code.** Concrete event classes will also define evaluation behavior.

A class can register its catalog definition without being instantiated:

```python
The180Club.register()
```

Registration uses the stable `code` to create a missing catalog record or update its descriptive metadata. It is separate from issuing a player award; calling `register()` never creates a `PlayerAchievement`.

### 5.1 Registration workflow

Proposed workflow:

1. Implement a Python achievement class.
2. Add it to an explicit achievement registry, initially containing event-based classes.
3. Execute a registration/synchronization operation to create or update catalog entries.
4. The evaluator can resolve the registered catalog entry by `code` when issuing awards.

A Django management command such as `python manage.py register_achievements` is the preferred candidate. **Do not register every catalog definition on each game submission.** Automatic deployment integration is deferred.

Because Python is authoritative, repeating registration can overwrite catalog metadata edited directly in Django Admin. Achievement codes must be treated as stable identifiers: changing a code would otherwise create a new catalog row instead of renaming the existing one.

## 6. Event-Based Evaluation and Reconciliation

### 6.1 Triggers

Invoke event evaluation after successful operations in the existing services:

- `create_game()` — after the game and its results are created.
- `update_game()` — after changes to the game and its results are saved.

**Confirmation status does not govern eligibility and is not a trigger.** Newly submitted results are eligible even when other players have not confirmed them.

### 6.2 Evaluation contract

The planned event evaluator is called with a game, conceptually:

```python
evaluate_game_achievements(game=game)
```

Individual event achievement classes should evaluate a game and identify qualifying `GameResult` records. Evaluation logic should not independently create or delete player-award rows.

### 6.3 Reconciliation procedure

For the affected game:

1. Load current `GameResult` records and related players.
2. Execute applicable registered event-achievement definitions.
3. Build the expected set of `(achievement, source_result, player)` awards.
4. Load existing event-based `PlayerAchievement` records associated with that game's results.
5. **Create** missing awards.
6. **Keep** existing awards that still qualify.
7. **Delete** awards that no longer qualify.

An edit can create a previously unearned award as well as remove an invalid one. A no-op re-evaluation must leave existing valid rows intact, including their original `awarded_at` timestamps.

Reconciliation must be limited to event-based achievement codes; it must not delete unrelated future time-boxed awards.

### 6.4 Corrections and deletions

Example: Susan enters a score of 181 and earns **The 180 Club**. Later she corrects it to 175. Re-evaluating that game deletes the corresponding earned-award row. If she subsequently corrects the score back to 181, a new row is created.

The current `update_game()` service treats a player reassignment as **delete old result + create new result**, which fits source-linked `CASCADE` deletion. Result deletion also automatically removes linked awards. Score, game-mode, or turn-order edits require the evaluator to reconsider applicable awards.

### 6.5 Transactions and efficiency

Both existing game-entry services use `@transaction.atomic`. The preferred integration is to run evaluation and award synchronization **inside the same transaction**, after all changes have been persisted, so a failure rolls back the game and award changes together.

The evaluator should reload current result data (or ensure prefetch caches are not stale) and avoid one query per player per achievement. Scoping work to the changed game is the first efficiency measure; a whole-history reconciliation is not part of routine event processing.

## 7. Suggested Code Organization

```text
portal/
    models.py                         # Achievement, PlayerAchievement
    services/
        achievements/
            base.py                   # Shared definition and registration contract
            event_achievements.py     # Concrete event-based rules
            registry.py               # Registered achievement classes
            event_evaluator.py        # Evaluate and reconcile one game
    management/
        commands/
            register_achievements.py  # Proposed catalog synchronization
```

Names and file boundaries are provisional. A separate generalized awarding service is **not required** for the first version. The event evaluator can orchestrate persistence, with small shared helpers added if they become useful.

## 8. Existing Game-Service Integration

Review of `game_entry.py` establishes that:

- `create_game()` creates the `Game`, then creates each populated `GameResult`, and returns the game.
- `update_game()` updates game fields, deletes or reassigns old results, updates surviving results, and creates new results.
- Player reassignment deletes the old `GameResult` and creates another rather than changing its `player_id` in place.
- Both services are transactional.

Integration should remain in the service layer, not in Django views or model signals. The evaluator runs once after the service has completed all modifications to the game's results.

## 9. Player Experience

Players will be able to see the earned awards associated with their player record. Possible surfaces include the account page, Player Overview, and a future dedicated profile/gallery.

For now, there is **no claim, acceptance, hide, manual removal, or revoked state**. Display details and notification behavior are outside this first implementation.

A player corrects an incorrectly earned event award by correcting the source game result; the evaluator then reconciles the database.

## 10. Future: Time-Boxed Achievements

Time-boxed achievements are a separate Python evaluation category. They are **not triggered by game submission**. A future scheduled process will evaluate completed periods such as a calendar month.

Examples include most competitive games in October or highest solo score in November.

The two-table catalog/recipient model is intended to be reusable, but period source fields, tie rules, late corrections, finalization, and uniqueness constraints remain **undecided**. No scheduled task is being implemented now.

## 11. Initial Implementation Plan

1. Add `Achievement` and `PlayerAchievement` models and constraints; create a migration.
2. Implement the Python base definition with `register()` and one example rule, **The 180 Club**.
3. Introduce the explicit registry and a catalog synchronization operation.
4. Implement the game-scoped event evaluator and award reconciliation.
5. Wire evaluation into `create_game()` and `update_game()`.
6. Test creation, repeated evaluation, correction in both directions, result deletion, player reassignment, game-mode changes, and transactional rollback.
7. Decide separately whether to backfill awards for existing historical games and how awards will be displayed.

## 12. Open Decisions

- Exact Python evaluation method signature and result type.
- Whether initial event achievement policies support only per-result repeatability or also once-per-player milestones.
- Final model deletion policies and any stricter consistency enforcement.
- How registration is invoked at deploy time, and how removed/renamed Python definitions are handled.
- Whether to perform a historical backfill of existing games at rollout.
- How future periodic awards identify their source and uniqueness key.
- User-facing presentation, artwork, and notifications.

---

## Current Design Summary

**Python defines and evaluates achievements; PostgreSQL stores a normalized catalog and earned-award relationships.** A class-level `register()` operation synchronizes each Python definition to `Achievement`. Game creation and editing trigger event-based evaluation immediately, without confirmation or scheduling. The evaluator reconciles `PlayerAchievement` rows associated with the changed game—creating newly qualified awards, retaining valid ones, and deleting invalid ones. Time-boxed evaluation remains a separate future workstream.
