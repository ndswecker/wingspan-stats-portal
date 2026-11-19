# Achievement System — Epic Specification (v2)

**Project:** Wingspan Stats Portal  
**Status:** v1 implemented and manually verified; v2 planned  
**Updated:** November 18, 2026

## 1. Purpose and Scope

The Achievement System recognizes accomplishments derived from recorded Wingspan games. Python classes define achievement rules; PostgreSQL stores an `Achievement` catalog and earned `PlayerAchievement` records.

**v1** supports awards earned independently for each qualifying game result. **v2** extends the system with awards earned **once per player per calendar month**, whether eligibility requires one qualifying game or a collection of games. Evaluation and reconciliation remain immediate when games are created, edited, or deleted.

The implementation stays inside the Django application. No scheduled worker, periodic finalization, or automatic historical backfill is required.

## 2. Existing v1 Baseline — Preserve

- `Achievement`: stable unique `code`, `name`, `description`. `BaseAchievement.register()` uses `update_or_create()` to synchronize metadata.
- An explicit registry (`EVENT_ACHIEVEMENTS`, `ALL_ACHIEVEMENTS`) and `register_achievements` management command synchronize definitions **at Docker startup, after migrations**. Registration never awards players or evaluates history.
- `PlayerAchievement`: recipient `player`, catalog `achievement`, nullable `source_result`, and `awarded_at`. The unique `(achievement, source_result)` constraint prevents duplicate per-result awards.
- `EventAchievement.evaluate(game=...)` returns qualifying `GameResult` records without writing awards. `The180Club` qualifies scores **at least 180**.
- `event_evaluator.py` reloads the game and current results from the database to avoid stale prefetched data; it creates missing awards, preserves valid awards, and deletes no-longer-valid awards for that game.
- `create_game()` and `update_game()` evaluate after results are persisted, inside their atomic transactions. `delete_game()` deletes source-linked awards through Django's cascading relationships.
- Eligibility is independent of `GameResult.is_confirmed`.
- Account page displays one card per earned achievement type with a count using `services/achievements/player_achievements.py` and the shared `includes/achievement_list.html` partial. Player Overview display is not implemented.
- Game deletion is available on Edit Game with confirmation. Server authorization uses `can_manage_game()`: game participants or staff; friendship/public visibility alone does not authorize management.
- **v1 manually verified:** qualifying/nonqualifying game creation; both directions of score correction; player reassignment; solo and competitive game deletion with award cascade; Account page with and without awards. Manual coverage is not exhaustive.

## 3. v2 Functional Requirements

### 3.1 Monthly award identity and eligibility

- Each monthly award is identified by **player + achievement definition + calendar month (year and month)**. It can be earned **at most once per month**, and again in later months.
- Use `Game.date_played` to determine the month, not the game entry timestamp or `awarded_at`.
- Evaluate immediately on game creation, update, or deletion; no month-end wait.
- Reevaluate affected periods after corrections. **Create** missing awards, **keep** valid ones without changing `awarded_at`, and **delete** awards that no longer qualify.
- Confirmation status does not affect eligibility.
- Solo and competitive modes use `Game.HumanPlayerMode.SINGLE` and `MULTIPLE`; participation is represented by `GameResult`. A player counts once per game.
- The month is stored with the earned award, **not embedded in the achievement's catalog code**. Display can format `November 2026 — Small Flock Solo`.

### 3.2 Initial milestone definitions (working names and thresholds)

| Stable code (proposed) | Game mode | Qualifies when player plays |
|---|---|---|
| `small_flock_solo` | Solo | 10 games in one month |
| `small_flock_competitive` | Competitive | 10 games in one month |
| `fallout_solo` | Solo | 30 games in one month |
| `fallout_competitive` | Competitive | 30 games in one month |

These names and thresholds are provisional. Reaching 30 games also satisfies the 10-game milestone for the same mode and month. Each milestone is a distinct achievement type.

### 3.3 Generality beyond game counts

The same monthly interface must also support rules based on individual games within the month. Example: **win a competitive game by more than 50 points** (beat the highest-scoring opponent by more than 50); award once in that month even if several games qualify. The evaluator checks whether **any qualifying game remains** after edits/deletions; it must not revoke the month's award merely because one of several qualifying games was changed.

Other monthly rules may aggregate scores, count distinct days played, or count wins. A monthly award's *earning frequency* does not dictate whether the eligibility rule checks one game or many.

## 4. v2 Architecture

### 4.1 Shared definitions and separate evaluation scopes

```text
BaseAchievement                 metadata and catalog registration
├── EventAchievement           per-game eligibility, one award per qualifying GameResult
└── MonthlyAchievement         player + calendar-month eligibility, at most one award/month
```

Keep the existing `EventAchievement` contract and evaluator. Introduce `MonthlyAchievement.evaluate(*, player: Player, period_start: date) -> bool` (proposed contract). The `period_start` is the first day of a calendar month. Concrete classes perform eligibility queries/logic only; evaluators own award persistence and reconciliation.

The registry adds `MONTHLY_ACHIEVEMENTS`, and `ALL_ACHIEVEMENTS` includes both categories for the existing registration command. Adding another monthly rule should require a class and registry entry, **not edits to game entry services**.

### 4.2 Orchestrator and change snapshots

Create an achievement orchestrator as the **single integration point** for game create/update/delete operations. It delegates to the existing per-game evaluator and a new monthly evaluator.

Capture **pre-change state before any modifications**: `date_played`, `human_player_mode`, and participating player IDs. A lightweight immutable `GameAchievementSnapshot` is sufficient. After changes, obtain the current state from persisted game/results. The previous state identifies scopes that could lose eligibility; the current state identifies scopes that could gain it.

| Operation | Before | After | Evaluation |
|---|---|---|---|
| Create | None | New game state | Event awards for new game; affected players/month |
| Update | Original game state | Updated game state | Event awards for updated game; union of old/new players and months |
| Delete | Original game state | None | Source-linked event awards cascade; reevaluate old players/month |

The orchestrator must reevaluate the **old and new** monthly scopes when the date or mode changes, and the **old and new participants** when player assignments change. Score edits can also affect monthly rules, even when month/mode/player IDs are unchanged. Do **not** calculate historical eligibility from a snapshot: use it only to identify what to recalculate against the **current database**.

A proposed single entry point is `synchronize_game_achievements(*, game: Game | None, previous_state: GameAchievementSnapshot | None)`. Snapshot capture and orchestration belong in the service layer, not views or Django signals. Run reconciliation within each existing `@transaction.atomic` game-operation transaction; update `delete_game()` to snapshot and orchestrate around deletion.

### 4.3 Monthly reconciliation

For each affected `(player, month)` scope:

1. Evaluate all registered monthly definitions against the **current** game history for that player and period.
2. Read existing monthly `PlayerAchievement` instances for the player, period, and registered definitions.
3. Create missing qualified instances; retain still-qualified instances; delete disqualified instances.
4. Never affect per-result event awards or unrelated players/periods.

A no-change reevaluation must be idempotent. Use ORM aggregation/`exists()` where suitable rather than materializing all a player's history. No whole-history scan on normal game changes.

### 4.4 Persistence and uniqueness

Extend `PlayerAchievement` with a nullable `period_start` (`DateField`) for monthly awards; first day of the month represents the month/year.

- **Event award:** `source_result` populated, `period_start` null; keep unique `(achievement, source_result)`.
- **Monthly award:** `source_result` null, `period_start` populated; add a database uniqueness constraint on `(player, achievement, period_start)` **conditioned on `period_start IS NOT NULL`**.
- Enforce the correct source/period pairing and first-day-of-month requirement through appropriate model/application validation and, where feasible, database constraints. Existing event records remain valid.
- `Achievement` catalog rows remain month-independent. Existing FK deletion rules remain unchanged: deleting a game cascades event awards; monthly awards require explicit reconciliation, **not** cascade via a single source result.

A migration is required. The concrete constraint and validation implementation will be settled when updating the model.

## 5. Registration and Historical Data

**Automatic Docker startup is limited to migrations and catalog registration.** It must **not** run achievement evaluation or historical award backfilling.

Optionally provide a **manual-only**, explicitly invoked Django management command to backfill or reconcile historical monthly awards. It should be idempotent and scoped appropriately (such as selected players/months or a deliberate date range). Historical backfill is **not a requirement for activating v2** and must never be triggered implicitly by deployment.

## 6. Player Display

Reuse the existing Account achievement summary and shared template. Monthly awards appear once per achievement type with a count of months earned, while per-game awards retain counts of qualifying games. The initial release need not add a month-by-month detail view, progress indicators, artwork, notifications, or Player Overview integration.

## 7. Implementation Sequence

1. Introduce `GameAchievementSnapshot` and `orchestrator.py`; route existing event evaluation through it. Manually verify v1 create, edit, player reassignment, and delete scenarios before proceeding.
2. Extend `PlayerAchievement` with monthly period identity and uniqueness; create/apply a migration.
3. Add `MonthlyAchievement`, its registry category, and a monthly evaluator/reconciler.
4. Implement the initial 10/30 solo/competitive monthly definitions.
5. Integrate previous/current state handling into create/update/delete with the orchestrator as the stable call site; preserve transactional behavior.
6. Update the Account display where necessary and manually verify counts.
7. Optionally implement a **manually invoked** historical backfill command.

## 8. Manual Acceptance Checklist (No Automated Tests in v2)

- [ ] Existing The 180 Club behavior survives the orchestration refactor.
- [ ] First through ninth games do not earn the 10-game milestone; tenth game awards it immediately.
- [ ] Thirtieth game awards the 30-game milestone without duplicating the 10-game award.
- [ ] Solo and competitive counts are independent; each player is counted once per game.
- [ ] Different months and years receive distinct awards; month boundaries are correct.
- [ ] Repeated reevaluation preserves one monthly award and its original `awarded_at`.
- [ ] Editing score, date, mode, or participants reevaluates affected monthly scopes; both old/new periods and participants are handled.
- [ ] Deleting a qualifying game removes monthly awards when the player falls below threshold; event awards still cascade normally.
- [ ] For a single-game-triggered monthly rule, removing one qualifying game does not revoke the award while another qualifying game remains.
- [ ] Account page displays the expected earned types and counts, including the no-awards state.
- [ ] Restarting/rebuilding Docker registers definitions only and does **not** backfill historical awards.

**Testing policy for this iteration:** manual user tests only. Automated test development is out of scope.

## 9. Proposed File Map

```text
portal/
  models.py
  services/
    game_entry.py
    achievements/
      base.py
      event.py
      event_achievements.py
      event_evaluator.py
      monthly.py                  # new base contract
      monthly_achievements.py     # new rules
      monthly_evaluator.py        # new monthly reconciliation
      orchestrator.py             # new shared change coordination
      registry.py
      player_achievements.py      # existing Account summary
  management/commands/
    register_achievements.py      # existing automatic catalog registration
    backfill_achievements.py      # optional, manual-only
  templates/portal/includes/
    achievement_list.html         # existing shared display
```

**v2 boundary:** establish extensible immediate monthly eligibility and reconciliation without changing how current event awards work, without scheduled processing, without automatic history backfills, and without an automated test suite.
