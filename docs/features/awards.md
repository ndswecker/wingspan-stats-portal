# Wingspan Portal — Achievement System

**Status:** Implemented; preparing for production  
**Updated:** November 21, 2026  
**Scope:** Event (per-game-result) and monthly (per-player-per-month) achievements

## 1. Purpose

Achievements recognize accomplishments derived from saved Wingspan games. Python classes define **what qualifies**; the Django service layer determines **when to evaluate and reconcile**; PostgreSQL records **what has been earned**.

The system is deliberately extensible: most new achievements require only a rule class and a registry entry. No scheduler, signals, separate service, or modification to the game-entry workflow is needed for these two supported achievement scopes.

## 2. Architecture

```text
BaseAchievement                       Shared metadata and catalog registration
├── EventAchievement                 Evaluate one game; return qualifying GameResults
│   ├── The180Club
│   ├── TheDodo
│   ├── TheShrike
│   └── TheImpaledShrew
└── MonthlyAchievement               Evaluate one player in one calendar month; return bool
    └── MonthlyGameCountAchievement   Reusable count-based monthly rule
        ├── BackyardBirderSolo
        ├── BackyardBirderCompetitive
        ├── HardcoreListerSolo
        └── HardcoreListerCompetitive
```

**Responsibilities**

| Component | Responsibility |
|---|---|
| Achievement rule classes | Declare `code`, `name`, `description`, and read-only eligibility logic |
| `registry.py` | Explicitly list implemented event and monthly rules; expose `ALL_ACHIEVEMENTS` |
| `register_achievements` management command | Synchronize catalog definitions using `BaseAchievement.register()` (`update_or_create` by stable code) |
| `event_evaluator.py` | Create, retain, or revoke per-result awards for a changed game |
| `monthly_evaluator.py` | Create, retain, or revoke monthly awards for one player/month |
| `snapshot.py` | Capture immutable pre-change and persisted post-change game scope |
| `orchestrator.py` | Identify affected scopes and delegate to evaluators |
| `game_entry.py` | Call the orchestrator inside atomic create/update/delete operations |
| `player_achievements.py` | Aggregate earned awards by achievement type for the Account page |

**Separation of concerns:** rule classes determine eligibility but do not create or delete `PlayerAchievement` rows. Evaluators own persistence and reconciliation. The orchestrator owns change scope, not individual award rules.

## 3. Data model and award identity

### `Achievement` — catalog definition

- `code`: immutable-in-practice, unique identifier; use `snake_case`.
- `name`, `description`: user-facing metadata, synchronized from code at registration.
- Catalog entries are not themselves earned awards.

### `PlayerAchievement` — earned instance

- `player`: recipient.
- `achievement`: catalog FK.
- `source_result`: nullable `GameResult` FK; populated for event awards.
- `period_start`, `period_end`: nullable dates; populated for monthly awards.
- `awarded_at`: timestamp when the record was created, **not** necessarily the date the game was played.

| Scope | Identity | `source_result` | `period_start` / `period_end` |
|---|---|---|---|
| Event | Achievement + qualifying `GameResult` | Populated | Null |
| Monthly | Player + achievement + calendar month | Null | Populated |

Database constraints prevent duplicate awards for the same event result and duplicate monthly awards for the same player/achievement/month. Source/period integrity and chronological period bounds are also constrained. The monthly end date is **exclusive**: November 2026 is `[2026-11-01, 2026-12-01)`.

A monthly award intentionally has **no source result**. The tenth or thirtieth game may trigger evaluation, but eligibility belongs to the player's **combined monthly history**, not to that one game. Deleting the triggering game should not delete an award if enough other qualifying games remain.

## 4. Current achievement catalog

### Event achievements

Every qualifying `GameResult` can earn its own instance. All are independent of result confirmation.

| Code | Name | Qualification |
|---|---|---|
| `the_180_club` | The 180 Club | Score **≥ 180** in one game |
| `the_dodo` | The Dodo | Score **< 80** in one game |
| `the_shrike` | The Shrike | In a competitive game with at least two results, be the sole winner and beat second place by **≥ 30** |
| `the_impaled_shrew` | The Impaled Shrew | In a competitive game with at least two results, finish **≥ 30** points below the highest score; multiple recipients possible |

The Shrike and Impaled Shrew compare human participants in the same game. A multiplayer game can award The Impaled Shrew without awarding The Shrike, because a distant trailing player may lose by 30 even when the winner beats second place by less than 30. A tie for first cannot earn The Shrike.

User-facing descriptions may be cheeky and bird-themed, but **qualification thresholds belong in `evaluate()`**, not in prose. The intended paired descriptions are:

- **The Shrike:** “Win by at least 30 points and leave your competition impaled on a thorn.”
- **The Impaled Shrew:** “Lose by at least 30 points and find yourself dangling from the shrike's barbed wire.”

### Monthly achievements

Monthly participation counts distinct games represented by a player's `GameResult` entries, using `Game.date_played`. Solo and competitive counts are independent; a player can earn both 10- and 30-game milestones for the same mode and month.

| Code | Name | Requirement in one calendar month |
|---|---|---|
| `backyard_birder_solo` | Backyard Birder — Solo | ≥ 10 solo games |
| `backyard_birder_competitive` | Backyard Birder — Competitive | ≥ 10 competitive games |
| `hardcore_lister_solo` | Hardcore Lister — Solo | ≥ 30 solo games |
| `hardcore_lister_competitive` | Hardcore Lister — Competitive | ≥ 30 competitive games |

Game modes are `Game.HumanPlayerMode.SINGLE` and `Game.HumanPlayerMode.MULTIPLE`. Month boundaries are start-inclusive and end-exclusive; December-to-January rollover is handled when computing boundaries. Confirmation status does not affect counting.

## 5. Eligibility contracts

### Event rules

```python
class ExampleEvent(EventAchievement):
    code = "example_event"
    name = "Example Event"
    description = "Example qualification."

    @classmethod
    def evaluate(cls, *, game: Game) -> list[GameResult]:
        # Return all qualifying GameResult instances.
        # Do not write achievement records here.
        return []
```

An event rule receives a game and returns **zero, one, or several qualifying results**. This supports score thresholds, winners' margins, tied scores, and other relationships among results. The evaluator reloads the game and results from the database to avoid stale prefetched relationships following edits or player reassignment.

### Monthly rules

```python
class ExampleMonthly(MonthlyAchievement):
    code = "example_monthly"
    name = "Example Monthly"
    description = "Example qualification for one calendar month."

    @classmethod
    def evaluate(
        cls, *, player: Player, period_start: date, period_end: date
    ) -> bool:
        # Read the current games in [period_start, period_end).
        # Do not create/delete achievement records here.
        return False
```

Monthly rules return whether the player qualifies **now** for that month. `MonthlyGameCountAchievement` implements the common count-based case via configurable `required_games` and `game_mode` class attributes. Future monthly rules may inspect any qualifying game, total scores, distinct play dates, or other aggregates without changing the evaluator's contract.

## 6. Lifecycle and reconciliation

```text
create_game / update_game / delete_game  [transaction.atomic]
    |
    +-- Capture previous GameAchievementSnapshot (update/delete)
    +-- Persist game and GameResults (or delete game)
    +-- synchronize_game_achievements(game, previous_state)
          |
          +-- For a surviving game: evaluate_game_achievements(game)
          |     +-- Create qualifying per-result awards
          |     +-- Preserve existing qualifying awards
          |     +-- Delete no-longer-qualifying awards
          |
          +-- Derive affected (player, month) scopes from
                previous and current persisted snapshots
                +-- evaluate_monthly_achievements(player, period)
                      +-- Create qualifying monthly awards
                      +-- Preserve existing qualifying awards
                      +-- Delete no-longer-qualifying awards
```

`GameAchievementSnapshot` contains `date_played`, `human_player_mode`, and a `frozenset` of player IDs. On update, the previous state is captured **before writes**; the current state is retrieved **after writes**. For deletion, the original state is retained, while the game and event awards are removed via cascade.

The orchestrator computes the **union** of previous and current affected `(player, month)` scopes. This handles:

- Creating a game: evaluate current participants/month.
- Correcting scores: reevaluate even when the participants and month are unchanged.
- Changing a date: reevaluate both the old and new months.
- Reassigning participants: reevaluate both removed and added players.
- Switching solo/competitive mode: reevaluate all monthly rules for affected players/month.
- Deleting a game: cascade its event awards and reevaluate the original participants/month.

**Reconciliation always queries current persisted game history.** Snapshots identify *where* to reevaluate; they are not used to derive historical eligibility. All work occurs inside the game operation's transaction, keeping game changes and awards consistent.

**Idempotency:** reevaluating unchanged data must not create duplicates or replace valid instances. A valid award keeps its original `id` and `awarded_at`. If eligibility disappears, delete the award; if eligibility later returns, create a new instance.

## 7. Adding or changing an achievement

1. **Choose scope.** Event if awarded per qualifying result; monthly if awarded at most once per player per calendar month.
2. **Define a class** in `event_achievements.py` or `monthly_achievements.py`. Supply stable `code`, user-facing metadata, and a read-only `evaluate()` implementation.
3. **Register the class** in `EVENT_ACHIEVEMENTS` or `MONTHLY_ACHIEVEMENTS` in `registry.py`. `ALL_ACHIEVEMENTS` combines both registries.
4. **Synchronize the catalog** by running `register_achievements` (normally performed during Docker startup, after migrations).
5. **Manually verify** boundary thresholds, appropriate recipients, creation, edit/revocation, delete behavior, and account/admin display.

For a new rule **within an existing scope**, no changes should be required to `game_entry.py`, `orchestrator.py`, evaluators, or models. Changing `name` or `description` for an existing stable code updates the catalog on registration. **Changing an `evaluate()` rule is consequential:** existing awards are only brought into line when their game or player/month scope is reevaluated; registration alone does not retroactively reconcile historical awards. Avoid reusing a stable code for an unrelated accomplishment.

To add a **new scope** (e.g. annual awards), design its identity, evaluator, registry, and orchestrator integration deliberately rather than forcing it into event/monthly logic.

## 8. Registration, deployment, and historical data

- Docker startup executes database migrations and `register_achievements`; registration synchronizes definitions **only**.
- No scheduled worker, month-end finalization, automatic backfill, or full-history scan runs on deployment.
- Subsequent game creation/edit/deletion reevaluates only its affected scopes. Editing an older game can legitimately reconcile its historical month.
- Any bulk historical reconciliation/backfill should be an **explicit, manually run operation**, scoped and reviewed separately. Such a command is optional, not part of the deployed feature.
- Deploy code and migration changes through the normal Django/Docker process; confirm new catalog entries exist before evaluating games against them.

## 9. Presentation and administration

- The Account page groups earned `PlayerAchievement` rows by achievement type and displays `earned_count`. For event rules, this represents qualifying game results; for monthly rules, qualifying months.
- `portal/includes/achievement_list.html` is the shared achievement display partial.
- In Django Admin, show `source_result` alongside `period_start` and `period_end`: event awards have a source result; monthly awards have period dates instead.
- A month-by-month achievement history, progress meter, popup notifications, and Player Overview award display are **not** currently part of this scope.

## 10. Minimal manual regression checklist

- [ ] Event boundaries: The 180 Club at 180; The Dodo at 79 but not 80.
- [ ] The Shrike triggers at a **30-point** winning margin (not only 31); ties do not qualify.
- [ ] The Impaled Shrew applies to **each** opponent at least 30 points behind first place.
- [ ] Editing scores removes awards no longer earned and adds newly earned awards.
- [ ] Monthly tenth game awards Backyard Birder; deleting it revokes the award if count falls below 10.
- [ ] A thirtieth game awards Hardcore Lister without duplicating Backyard Birder.
- [ ] Moving a game across months or changing participants/mode reconciles old and new scopes.
- [ ] Repeating evaluation preserves valid award IDs/timestamps and does not duplicate records.
- [ ] Account counts and Admin source/period columns match expected awards.
- [ ] Restarting Docker registers catalog definitions but does not backfill historical games.

**Verified in development during this feature work:** event-score awards and their revocation; monthly award persistence and idempotency; tenth-game monthly award creation and removal after deleting the game. Broader scenarios above remain useful pre-deployment regression checks.

## 11. File map

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
      monthly.py
      monthly_achievements.py
      monthly_evaluator.py
      snapshot.py
      orchestrator.py
      registry.py
      player_achievements.py
  management/commands/
    register_achievements.py
  templates/portal/includes/
    achievement_list.html
```

**Maintenance principle:** keep eligibility rules isolated in classes, catalog registration explicit, reconciliation centralized, and earned awards derived from current database truth.
