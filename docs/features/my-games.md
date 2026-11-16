# Wingspan Portal — My Games

**Status:** Approved for Development  
**Scope:** Personal game history and management  
**Target Version:** TBD

---

## 1. Objective

Introduce a dedicated **My Games** page that allows authenticated players to easily find, review, and manage games they participated in.

Replace the existing top-level **Add Game** navigation item with **My Games**, making `/games/` the central location for personal game management.

Keep game creation and editing as separate workflows accessible from this area.

The feature must preserve existing game-entry permissions, editing behavior, and score-confirmation rules.

## 2. Functional Requirements

### Navigation and Game Creation

- Replace the top-level Add Game navigation item with **My Games**.
- Route My Games to `/games/`.
- Display a prominent **+ Add New Game** button linking to the existing Add Game page.
- Keep the existing Add Game and Edit Game pages separate.
- After successfully creating a game, redirect to the newly created game's **Edit Game** page.
- Preserve existing game creation and editing functionality.

### Game Selection

My Games displays only games in which the authenticated user's linked `Player` participated.

- Identify the player from the authenticated Django user.
- Include Solo and Competitive games.
- Include games regardless of confirmation status.
- Do not provide a player-selection control.
- Do not include games in which the authenticated player did not participate.

A game qualifies when it has a `GameResult` associated with the authenticated player.

### Filters

Provide the following filters:

| Filter | Options / Behavior |
|---|---|
| Game Type | All Games, Solo, Competitive |
| Start Date | Optional; inclusive |
| End Date | Optional; inclusive |

**Default behavior:**

- Game Type: All Games
- Start Date: Blank
- End Date: Blank
- Display all matching historical games, newest first.

Both date fields may be left empty. An empty start date includes games from the beginning of recorded history; an empty end date imposes no upper date bound.

Validate that the end date is not earlier than the start date.

Provide a Reset Filters action.

### Sorting and Pagination

- Sort by `date_played` descending.
- Use Game ID descending as the secondary sort.
- Display 50 games per page.
- Preserve selected filters when navigating between pages.
- Display a simple empty-state message when no games match the selected filters.

Suggested message:

> No games match the selected filters.

## 3. Game List

Display a responsive table of games with the following columns:

| Column | Description |
|---|---|
| Game ID | Unique game identifier |
| Date Played | Date the game occurred |
| Game Type | Solo or Competitive |
| My Score | Authenticated player's score |
| Players | Names of all recorded participants |
| My Confirmation | Confirmation status of the authenticated player's result |
| Game Confirmation | Whether every participant has confirmed their result |
| Action | Edit Game link |

Every row must link to the existing Edit Game page for that game.

The page is intended for game management rather than statistical analysis. No aggregate statistics or charts are required.

## 4. Confirmation Status

Display two independent confirmation indicators.

### My Confirmation

Derived from the authenticated player's `GameResult.is_confirmed`.

- **Confirmed:** The authenticated player's result is confirmed.
- **Pending:** The authenticated player's result is not confirmed.

### Game Confirmation

Derived from all `GameResult` records associated with the game.

- **Fully Confirmed:** Every recorded participant has confirmed their result.
- **Pending:** One or more participants have unconfirmed results.

Games must remain visible in My Games regardless of either confirmation status.

Confirmation indicators are informational and must reflect current database values.

No additional game-level confirmation field is required.

## 5. Game Editing and Permissions

Every listed game contains a result belonging to the authenticated player.

- Provide an Edit Game link for every listed game.
- Continue using the existing `game_edit()` view.
- Preserve the existing `can_manage_game()` authorization check.
- Do not introduce new editing permissions or confirmation rules.
- Preserve existing behavior when results are changed, added, reassigned, or removed.

The My Games listing must never expand access to games in which the authenticated player did not participate.

## 6. Technical Architecture

### Data Models

Use the existing models:

- `Game`
- `GameResult`
- `Player`

The existing relationships already support the feature.

No database schema changes or migrations are anticipated.

### Game Selection Service

Introduce a focused service responsible for retrieving the authenticated player's games.

The service should:

- Select games through the player's associated `GameResult` records.
- Apply optional game-type and date filters.
- Include both confirmed and unconfirmed games.
- Retrieve associated players and results efficiently.
- Support the information needed for individual and whole-game confirmation status.
- Return games in the agreed sorting order.

Keep this service separate from statistics-oriented result selection, where fully confirmed games may be required.

### Forms

Add a dedicated `MyGamesFilterForm` in `portal/forms.py`.

The form handles game type, optional date boundaries, and date-range validation.

No player-selection field is needed.

### Views

Add a My Games listing view in `portal/views/games.py`.

Responsibilities:

- Require authentication and a linked Player.
- Validate GET filter parameters.
- Retrieve matching games through the selection service.
- Paginate results at 50 games per page.
- Render the My Games template.

Update `GameCreateView` so successful submissions redirect to the newly created game's Edit Game page.

Do not duplicate game-editing or confirmation logic in the listing view.

### Templates and URLs

| File | Responsibility |
|---|---|
| `portal/forms.py` | `MyGamesFilterForm` |
| `portal/services/` | Personal game-selection service |
| `portal/views/games.py` | My Games view and creation redirect |
| `portal/templates/portal/my_games.html` | Filters, game list, confirmation indicators, pagination |
| `portal/templates/portal/base.html` | Replace Add Game navigation with My Games |
| `portal/urls.py` | Register `/games/` |

Existing Add Game, Edit Game, Game Detail, and HTMX endpoints should remain functional.

## 7. Implementation Considerations

### Query Efficiency

Avoid querying the database separately for each listed game's participants or confirmation status.

Use Django's related-object querying and prefetching appropriately.

### Confirmation Integrity

Derive whole-game confirmation from every associated `GameResult`.

A player's own confirmed score does not imply that the entire game is fully confirmed.

### Filtering and Pagination

Apply filtering and sorting before pagination.

Preserve filter parameters across pagination links.

Handle invalid filter submissions and out-of-range page numbers gracefully.

### Authorization

Derive the selected player exclusively from the authenticated user.

Never accept a player ID from GET parameters to determine whose games are listed.

Continue enforcing editing permissions in the existing Edit Game view.

### Responsive Layout

The table must remain usable on mobile devices, including games with multiple participants and longer player names.

Follow the portal's existing Bootstrap styling conventions.

## 8. Implementation Sequence

1. Create `MyGamesFilterForm`.
2. Implement the personal game-selection service.
3. Add the `/games/` listing view and pagination.
4. Build `my_games.html`.
5. Update the navigation in `base.html`.
6. Redirect successful game creation to Edit Game.
7. Test filtering, pagination, participant information, confirmation statuses, and editing links.
8. Verify existing Add Game and Edit Game workflows remain functional.
9. Deploy after successful testing.

## 9. Acceptance Criteria

The feature is complete when:

- My Games replaces Add Game in the main navigation.
- `/games/` displays games belonging to the authenticated player without additional selection.
- Both confirmed and unconfirmed games appear.
- All Games, Solo, and Competitive filters work correctly.
- Optional date filtering and Reset Filters work correctly.
- Results are sorted newest first and paginated at 50 per page.
- Every game displays its ID, date, type, the user's score, and all participants.
- Personal confirmation and whole-game confirmation statuses are accurate.
- Every listed game provides a working Edit Game link.
- **+ Add New Game** opens the existing creation form.
- Successfully creating a game redirects to its Edit Game page.
- Existing game editing, friendship permissions, and confirmation rules remain unchanged.
- No database migration is required.

---

**Release principle:** Make personal game management directly accessible and intuitive while preserving the existing game-data architecture, authorization boundaries, and confirmation workflow.