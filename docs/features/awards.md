# Achievement System — Epic Specification and v1 Release Baseline

**Project:** Wingspan Stats Portal  
**Epic:** Achievement System  
**Release:** v0.5.0 — Event-Based Awards and Personal Achievement Display  
**Status:** v1 implementation complete; production release pending final checks  
**Updated:** November 18, 2026

## 1. Purpose

Recognize player accomplishments based on recorded Wingspan games. An **achievement** is a cataloged accomplishment; a **player award** (`PlayerAchievement`) is an earned instance associated with a player and, for event achievements, a source game result.

The Achievement System is an ongoing epic. Version 1 establishes an event-based award pipeline and displays earned achievement summaries on the Account page. Additional achievement categories and viewing surfaces are future increments.

## 2. Version 1 — Delivered Scope

### 2.1 Data model

- `Achievement`: unique stable `code`, `name`, and `description`.
- `PlayerAchievement`: `player`, `achievement`, optional `source_result`, and `awarded_at`.
- Uniqueness of `(achievement, source_result)` prevents duplicate awards for the same qualifying game result.
- Foreign-key behavior: player deletion cascades to awards; achievement definition deletion is protected; game-result deletion cascades to source-linked awards.
- Multiple game results may earn the same achievement, including multiple awards for one player across different games.

### 2.2 Definitions and registration

- Python classes define achievement codes, metadata, and eligibility rules; PostgreSQL stores definitions and earned awards.
- `BaseAchievement.register()` uses `update_or_create(code=..., defaults=...)` to synchronize name and description.
- Achievement codes are stable identifiers and must not be casually renamed.
- An explicit registry holds achievement classes (`EVENT_ACHIEVEMENTS`, `ALL_ACHIEVEMENTS`).
- The `register_achievements` Django management command runs during Docker startup after migrations. Registration is independent of game evaluation and does not rescan player awards.

### 2.3 Event-based award evaluation

- `EventAchievement.evaluate(game=...)` returns qualifying `GameResult` records; concrete rules perform no award writes.
- `The180Club` is the first defined achievement: score **at least 180** in a single game (`the_180_club`).
- `evaluate_game_achievements(game=...)` processes registered event-based rules, creates missing `PlayerAchievement` rows, preserves still-valid awards, and deletes no-longer-valid awards for the affected game.
- The evaluator reloads the current game and its related results from the database to avoid stale `prefetch_related()` caches when the editing flow deletes/reassigns results.
- Evaluation runs after all results are saved inside the `create_game()` and `update_game()` service transactions, regardless of score confirmation status.
- There is no automatic full-history evaluation at Docker startup.

### 2.4 Game deletion integration

- A Delete Game action exists on the Edit Game page with a confirmation modal and distinct POST action.
- The same edit view enforces `can_manage_game()` before handling edits or deletion. The permitted set is game participants or staff; friendship and public visibility alone do not authorize deletion. Standard staff/superuser account behavior applies.
- A transactional `delete_game()` service deletes the game. Django cascades deletion through game results to source-linked awards; achievement catalog entries remain intact.
- Removing the final result through the regular edit form remains disallowed; deleting the entire game is the separate supported operation.

### 2.5 Account page display

- A shared retrieval function, `services/achievements/player_achievements.py::get_player_achievement_summary()`, groups a player's earned awards by achievement code/name/description and counts instances in PostgreSQL.
- The reusable `portal/includes/achievement_list.html` partial displays each earned achievement type with its name, description, and earned count.
- The Account page displays the logged-in player's lifetime achievement summary, including an empty state when no awards exist.
- A separate Player Overview achievement section has **not** been implemented.

## 3. Version 1 Behavior and Boundaries

- Awards are issued automatically; players do not claim, accept, hide, or manually remove them.
- Correcting a qualifying score below its threshold removes the award. Restoring eligibility creates a new award record and `awarded_at` timestamp.
- Awards are tied to `GameResult` evidence, not to a game directly. Deleting or replacing a qualifying result removes the original award; a new qualifying result may earn a new award.
- `is_confirmed` does not control achievement eligibility.
- The Account page shows earned types only. It does not list locked/unearned achievements, individual source games, or award-history detail.
- The first achievement is repeatable per qualifying result; once-per-player, nonrepeatable and periodic policies are not yet supported.
- No notifications, badge artwork, tiers, points, leaderboards, or background job scheduler are included.

## 4. Validation Performed

The following cases were manually exercised in development:

| Scenario | Result |
|---|---|
| Create qualifying game (181) | Award created |
| Create nonqualifying game (179) | No award |
| Edit score from qualifying to nonqualifying | Award removed |
| Edit score from nonqualifying to qualifying | Award created |
| Reassign player on qualifying game result | Worked after fixing stale prefetched game results |
| Delete solo game | Game deleted |
| Delete competitive game | Game deleted |
| Delete game with associated awards | Source-linked awards cascaded |
| Account with award | Award summary displayed |
| Account without awards | Empty state displayed |

**Validation limits:** These are manual results reported during development, not evidence of an automated regression-test suite. An unauthorized deletion attempt has not been reported as explicitly tested. Exact repeat-evaluation/idempotence and transaction-failure rollback have not been verified by dedicated automated tests.

## 5. Production Release Checklist

### Required before deploying

- [ ] Review Git diff, confirm migrations and all achievement files are committed, and check Django system checks.
- [ ] Confirm the running migration includes `Achievement` and `PlayerAchievement` and the registration command is called after migrations.
- [ ] Verify an authenticated nonparticipant receives HTTP 403 on a forged game-delete POST; verify participants and staff can delete.
- [ ] Verify the production template includes the modal's CSRF-protected form and normal game editing still succeeds.
- [ ] Confirm that no temporary test games or test awards are being mistaken for genuine player history.
- [ ] Back up the production PostgreSQL database before deploying.
- [ ] Choose and document the historic-game backfill policy (see below).
- [ ] Deploy the committed changes through the existing Git / Docker Compose production procedure and inspect startup logs for migrations and achievement registration.
- [ ] Smoke-test Account achievement display and creation/editing/deletion with a controlled game on production.

### Historical games — explicit release decision

**No automatic historical backfill is included in v1.** New or edited games are evaluated; preexisting games remain unevaluated unless edited or processed through a deliberate, separate backfill. Therefore initial counts may understate lifetime qualifications. Consider backfilling later with a one-time, idempotent management command, after validating performance, permissions, and reconciliation behavior against existing data.

## 6. Epic Backlog — Future Increments

### Next: Player-facing access

- Add lifetime achievement summaries to Player Overview using the existing player visibility/permission rules, not public visibility as a deletion/edit authorization mechanism.
- Reuse the achievement summary service and shared partial.
- Decide whether the overview should show lifetime achievements or reflect date/game-type filters; the prior discussion favored lifetime totals for consistency, but no implementation decision is finalized.
- Optionally show award dates and links to source games, with access controls on any linked details.

### New event achievements

- Add additional per-game rule classes and register them explicitly.
- Define repeatability/one-time award policies, tie behavior, and rules requiring comparison among game participants.
- Consider richer achievement metadata such as categories, display order, and artwork only when the catalog grows.

### Historical reconciliation and test coverage

- Add automated Django tests for creation, repeated evaluation, score corrections, result reassignment/deletion, full game deletion, permissions, and transaction rollback.
- Implement an explicit historical backfill/reconciliation tool if desired; do not couple it to ordinary Docker startup.
- Revisit query batching only when achievement volume warrants it.

### Periodic and long-horizon achievements

- Introduce a `PeriodicAchievement` evaluation category with scheduled or explicit period-finalization processing.
- Decide how a period is identified and how unique awards are enforced when `source_result` is null.
- Specify tie rules, late game corrections, award revocation after period closure, and period recalculation.

### Optional experience enhancements

- Dedicated achievement gallery; unearned achievements; rarity or progress indicators.
- Achievement notifications, badge artwork, award history, and source-game drill-down.
- Admin/support tools for reviewing unexpected awards, without allowing players to manually claim or remove awards.

## 7. Architecture and Code Map

```text
portal/
  models.py                                  Achievement, PlayerAchievement
  permissions.py                             can_manage_game()
  services/
    game_entry.py                            create_game(), update_game(), delete_game()
    achievements/
      base.py                                BaseAchievement, catalog registration
      event.py                               EventAchievement contract
      event_achievements.py                 The180Club rule
      event_evaluator.py                    game-scoped reconciliation
      player_achievements.py                grouped player summary
      registry.py                           EVENT_ACHIEVEMENTS, ALL_ACHIEVEMENTS
  management/commands/
    register_achievements.py                catalog synchronization
  views/
    games.py                                Edit Game and delete action
    account.py                              personal achievement summary
  templates/portal/
    game_edit.html                          delete confirmation modal
    account.html                            My Achievements section
    includes/achievement_list.html         reusable summary cards
```

## 8. Release Summary

**v1 is a viable first increment of the Achievement System epic.** Python defines and evaluates achievements; PostgreSQL retains catalog entries and earned instances. The portal automatically maintains event-based awards when games are created, edited, or deleted, and shows earned totals on the authenticated player's Account page. Player Overview, additional achievement types, historical backfill, automated regression coverage, and periodic awards remain separate work items.
