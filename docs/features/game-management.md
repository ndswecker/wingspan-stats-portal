# Feature Specification: Game Management and Result Confirmation

> **Project status:** This feature is considered complete for its
> current scope. Wingspan Portal as a product is still under active
> development and is not considered fully shipped or complete.

## Purpose

Allow players to view and correct recorded games while protecting the
integrity of each player's score.

A `Game` and its associated `GameResult` records are separate database
models, but the portal presents them as one game-management workflow.

This document reflects the completed feature as implemented. Whole-game
deletion and success-message popups are not part of the completed scope.

------------------------------------------------------------------------

## Completed User Stories

-   As a player, I can view the details of a recorded game.
-   As a player, I can edit a game in which I participated.
-   As a player, I can edit, add, or remove results within a game I
    participated in.
-   As a player, I can see whether each result has been confirmed by its
    player.
-   As a player, I can review and explicitly confirm my own recorded
    result.
-   As a player, I can see unconfirmed results associated with me from
    my Account page.
-   As staff, I can edit any game regardless of participation.
-   As a user, I can navigate from Competitive History to Game Detail.

------------------------------------------------------------------------

## Navigation

### Competitive History

The former **Game History** feature is now named **Competitive
History**.

Competitive History remains result-oriented and focused on competitive
games. A result entry can link to the corresponding Game Detail page,
where the complete game and all participating players' results are
shown.

The feature uses the `competitive_history` naming convention for its
route and view.

### Game Detail

The Game Detail page is a neutral, shared destination that may be
reached from multiple workflows, including Competitive History and the
Account page.

The page displays:

-   Game ID
-   Date played
-   Game type
-   All player results
-   Score
-   Turn order, when available
-   Result confirmation status

Authorized users are provided an **Edit Game** action.

A logged-in player with an unconfirmed result in the displayed game is
provided a **Confirm My Result** action for their own result only.

The page also provides navigation to **Competitive History**.

### Edit Game

Editing is performed through a single game-level workflow.

The edit page allows an authorized user to:

-   Change game fields such as date or game type.
-   Change existing scores.
-   Change turn order.
-   Add players/results.
-   Remove players/results.
-   Save all changes as one operation.

There is no separate GameResult edit page.

After a successful edit, the user is redirected to Game Detail.

Explicit confirmation is not performed from the Edit Game form.
Confirmation has its own narrow action on Game Detail. Score edits still
affect confirmation automatically according to the confirmation rules
below.

------------------------------------------------------------------------

## Authorization

A user may manage a game when:

-   Their linked `Player` has a `GameResult` for the game, or
-   `user.is_staff` is true.

Authorization is enforced server-side.

Staff may edit any game through the portal even when they did not
participate.

Only the player who owns a `GameResult` may explicitly confirm that
result. Staff privileges do not allow staff to confirm another player's
result.

A staff user may confirm a result only when that staff account is linked
to the `Player` who owns that result.

If a participant edits a game and removes their own result,
authorization is evaluated against the pre-edit game state. The save may
complete, after which that user no longer has participant-based
management rights to the game unless they are staff.

------------------------------------------------------------------------

## Game Integrity

The existing structural rules remain authoritative:

-   Solo games require exactly one result.
-   Competitive games require at least two results.
-   A player may appear only once per game.
-   Provided turn orders must be unique within the game.
-   Turn order may be blank.
-   Existing field validation, such as valid scores and dates, continues
    to apply.

Changing game type is permitted only when the final result set satisfies
the selected game type.

Game and GameResult changes are **atomic**. A failed validation must
leave the entire game unchanged.

### Adding and Removing Results

Authorized users may add or remove results while editing a game.

An edit may not leave the game structurally invalid. This means, for
example, that a competitive game cannot be saved with fewer than two
results and a solo game cannot be saved with more than one result.

Changing the player assigned to an existing result is treated as removal
of the old player's result and creation of a result for the new player.

Existing inactive players remain available when editing their historical
result. New result rows are limited to active players.

------------------------------------------------------------------------

## Result Confirmation

`GameResult` includes confirmation state:

``` python
is_confirmed = models.BooleanField(default=False)
```

Confirmation means:

> The player acknowledges participation in this game and confirms that
> the score recorded for them is correct.

Confirmation does **not** mean approval of all game metadata or other
players' results.

### Automatic Confirmation Rules

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
-   Adding or removing another participant

When the player assigned to a result changes, the old result is removed
and a new result is created. The new result is confirmed only when the
acting player is also the new result owner.

`is_confirmed` is not exposed as a normal editable GameResult form
field. Confirmation transitions are controlled by application business
logic.

### Explicit Confirmation

Explicit confirmation is performed from Game Detail rather than from
Edit Game.

The workflow is:

``` text
Account
    ↓
Pending Confirmation
    ↓
View Game
    ↓
Game Detail
    ↓
Confirm My Result
    ↓
POST confirmation action
    ↓
Game Detail
```

The confirmation endpoint:

-   Requires authentication.
-   Accepts POST requests only.
-   Operates on one `GameResult`.
-   Resolves the logged-in user's linked `Player`.
-   Verifies that the acting player owns the result.
-   Sets only that result's `is_confirmed` state to `True`.
-   Redirects back to Game Detail.

A user cannot confirm another player's result through the UI or by
manipulating the confirmation URL.

------------------------------------------------------------------------

## Account Page

The Account page acts as a personal management dashboard.

It includes a dedicated **Pending Confirmation** section containing
unconfirmed `GameResult` records belonging to the authenticated user's
linked `Player`.

Each pending item displays only the information needed to identify and
review it:

-   Game date
-   Player's recorded score
-   Link to Game Detail

The Account page does not provide a direct confirmation button. The
player must open Game Detail and review the complete game before
explicitly confirming their result.

Once a result is confirmed, it no longer appears in Pending Confirmation
because the Account query selects only results where:

``` python
is_confirmed=False
```

An unconfirmed `GameResult` therefore acts as the notification mechanism
for this feature. A separate notification model is not required.

Players without user accounts may accumulate unconfirmed results. If an
account is later linked to that `Player`, those pending results can then
be surfaced on the Account page.

A future **My Game Results** feature may provide a complete personal
ledger of solo and competitive results. That is separate from the
Account pending-confirmation dashboard and from Competitive History.

------------------------------------------------------------------------

## Game Deletion

Whole-game deletion is **not part of the completed feature scope**.

Although deletion was considered during initial design, the business
rules were not sufficiently defined for a shared game record. Deleting a
`Game` would also affect `GameResult` records belonging to other
participants, raising unresolved questions about ownership, consent,
confirmed results, staff authority, and whether deletion should instead
be represented by an archive or void state.

Game deletion is therefore deliberately deferred rather than treated as
incomplete implementation.

Any future deletion, archive, or void workflow should receive its own
requirements review before implementation.

------------------------------------------------------------------------

## Completed Implementation Areas

The completed feature includes:

1.  `GameResult.is_confirmed` confirmation state.
2.  Reusable game-management authorization.
3.  Shared structural validation for game results.
4.  Atomic Game + GameResult update behavior.
5.  Confirmation-state transitions during score/result edits.
6.  Public Game Detail view and template.
7.  Authorized Game Edit workflow.
8.  Competitive History links to Game Detail.
9.  Account-page Pending Confirmation query and display.
10. Dedicated POST-only explicit confirmation action.
11. Server-side ownership enforcement for explicit confirmation.
12. Competitive History naming and routing cleanup.

The implementation reuses existing game/result validation where
practical rather than maintaining competing structural rules.

------------------------------------------------------------------------

## Deliberately Excluded

The completed feature does not include:

-   Whole-game deletion.
-   Game archive or void workflows.
-   Success-message popups after edit or confirmation.
-   Game revision/history tracking.
-   Detailed audit logs.
-   A dispute-resolution system.
-   Separate GameResult detail/edit pages.
-   A separate notification model.
-   Player confirmation of another player's result.
-   A complete personal **My Game Results** browser.

These may be introduced as separate features later without changing the
core principle that confirmation belongs to an individual player's
`GameResult`.

------------------------------------------------------------------------

## Completion Status

**Game Management and Result Confirmation is complete for the currently
accepted scope.**

The implemented workflow supports viewing games, authorized correction
of game data and results, structural integrity, per-result confirmation
ownership, explicit self-confirmation, pending-confirmation management,
and navigation through Competitive History.

Whole-game deletion and success-message popups were intentionally
removed from the accepted scope rather than left as unfinished
requirements.
