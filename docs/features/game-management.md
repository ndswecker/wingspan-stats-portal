# Feature Specification: Game Management and Result Confirmation

## Purpose

Allow players to view and correct recorded games while protecting the
integrity of each player's score.

A `Game` and its associated `GameResult` records are separate database
models, but the portal should present them as one game-management
workflow.

------------------------------------------------------------------------

## User Stories

-   As a player, I can view the details of a recorded game.
-   As a player, I can edit a game in which I participated.
-   As a player, I can edit, add, or remove results within a game I
    participated in.
-   As a player, I can delete a game I participated in.
-   As a player, I can see whether each result has been confirmed by its
    player.
-   As a player, I can confirm that my own recorded score is correct.
-   As a player, I can see unconfirmed results associated with me from
    my Account page.
-   As staff, I can edit or delete any game regardless of participation.

------------------------------------------------------------------------

## Navigation

### Game History

Each game-result card on Game History links to its corresponding Game
Detail page.

Game History remains result-oriented: the card represents that player's
performance, but the link opens the complete game.

### Game Detail

The Game Detail page displays:

-   Game ID
-   Date played
-   Game type
-   All player results
-   Score
-   Turn order, when available
-   Result confirmation status

Authorized users are provided an **Edit Game** action.

### Edit Game

Editing is performed through a single game-level workflow.

The edit page allows an authorized user to:

-   Change game fields such as date or game type.
-   Change existing scores.
-   Change turn order.
-   Add players/results.
-   Remove players/results.
-   Confirm their own result.
-   Save all changes as one operation.

There is no separate GameResult edit page.

After a successful edit, redirect to Game Detail and display a success
message.

------------------------------------------------------------------------

## Authorization

A user may manage a game when:

-   Their linked `Player` has a `GameResult` for the game, or
-   `user.is_staff` is true.

Authorization must be enforced server-side.

Staff may edit or delete any game.

Only the player who owns a `GameResult` may confirm that result. Staff
privileges do not allow staff to confirm another player's score.

------------------------------------------------------------------------

## Game Integrity

The existing structural rules remain authoritative:

-   Solo games require exactly one result.
-   Competitive games require at least two results.
-   A player may appear only once per game.
-   Provided turn orders must be unique within the game.
-   Existing field validation, such as valid scores and dates, continues
    to apply.

Changing game type is permitted only when the final result set satisfies
the selected game type.

Game and GameResult changes must be **atomic**. A failed validation must
leave the entire game unchanged.

### Removing Results

Results may be removed while editing a game, but an edit must not leave
the game structurally invalid.

The special case where a player needs to remove their own result for
score-integrity reasons but doing so would invalidate the game should be
handled deliberately during implementation rather than bypassing
structural validation.

------------------------------------------------------------------------

## Result Confirmation

Add confirmation state to `GameResult`:

``` python
is_confirmed = models.BooleanField(default=False)
```

Confirmation means:

> The player acknowledges participation in this game and confirms that
> the score recorded for them is correct.

Confirmation does **not** mean approval of all game metadata or other
players' results.

### Confirmation Rules

When a player creates a result for themselves:

-   The result is confirmed.

When a player creates a result for another player:

-   The result is unconfirmed.

When a player changes their own score:

-   Their result becomes confirmed.

When another player or staff member changes a player's score:

-   That player's result becomes unconfirmed.

Changing unrelated information does not invalidate confirmation. This
includes:

-   Game date
-   Turn order
-   Another player's score
-   Adding/removing another participant

`is_confirmed` must not be exposed as a normal editable GameResult
field.

On the Edit Game page, only the authenticated player's own result may
provide a confirmation control.

------------------------------------------------------------------------

## Account Page

The Account page should surface unconfirmed `GameResult` records
belonging to the authenticated user's linked `Player`.

Each pending result should provide enough information to identify the
game and a link to its Game Detail page.

An unconfirmed `GameResult` acts as the notification mechanism for this
feature. A separate notification model is not required.

Players without user accounts may accumulate unconfirmed results. If
they later receive an account linked to that `Player`, those results can
then be surfaced.

------------------------------------------------------------------------

## Game Deletion

Authorized participants and staff may delete an entire game.

Deletion requires an explicit confirmation step.

Deleting a `Game` also deletes its associated `GameResult` records
through the existing cascade relationship.

After deletion, redirect to Game History and display a success message.

------------------------------------------------------------------------

## Implementation Direction

Keep business rules outside templates and minimize duplication between
creation and editing.

Expected implementation areas:

1.  Model migration for `GameResult.is_confirmed`.
2.  Game-management authorization helper/service.
3.  Game update service responsible for atomic Game + GameResult changes
    and confirmation rules.
4.  Game Detail view/template.
5.  Game Edit view/form/template.
6.  Game deletion workflow.
7.  Game History links to Game Detail.
8.  Account-page query/display for unconfirmed results.
9.  Tests for authorization, structural validation, confirmation
    transitions, and atomic updates.

Reuse existing game/result validation where practical rather than
creating competing rules.

------------------------------------------------------------------------

## Out of Scope

This feature does not introduce:

-   Game revision/history tracking.
-   Detailed audit logs.
-   A dispute-resolution system.
-   Separate GameResult detail/edit pages.
-   A separate notification model.
-   Player confirmation of another player's result.

These may be added later without changing the core principle that
confirmation belongs to an individual player's `GameResult`.
