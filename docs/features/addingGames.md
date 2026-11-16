# Wingspan Portal — Dynamic Game Player Entry

**Status:** Approved for Development  
**Scope:** Game creation workflow  
**Target Version:** TBD

---

## 1. Objective

Improve the Add Game workflow by replacing the current five permanently displayed player-result slots with a dynamic interface.

Users should begin with one player entry and add or remove additional players as needed.

The implementation will use Django forms, Django formsets, server-rendered HTML templates, and HTMX. No custom JavaScript is required.

The feature must preserve existing game validation, player permissions, and score-confirmation behavior.

## 2. Functional Requirements

### Player Entry

- The Add Game form initially displays one player-result row.
- Each row contains Player, Score, and optional Turn Order.
- An **Add Another Player** button dynamically adds another row.
- Additional rows include a **Remove** control.
- A maximum of five human players may be entered.
- At least one human player is required.
- Adding or removing rows must preserve previously entered values.
- Add/Remove operations must not save a game or create database records.
- The interface must work on desktop and mobile.

### Game Modes

Preserve the existing distinction between game modes:

- **Solo Game:** Exactly one human player.
- **Competitive Game:** Two or more human players.

Game mode is determined by the number of human participants, not the total number of participants.

The application may eventually support computer players. The current feature will not implement computer participants, but its design must not prevent their future inclusion.

### Validation

Preserve existing validation requirements:

- Every populated result requires a player and score.
- Scores must be nonnegative.
- Players cannot appear more than once in a game.
- Provided turn orders must be unique and positive.
- Game mode must agree with the human player count.
- Only the authenticated player and their eligible friends may be selected.

All validation must remain authoritative on the server.

### Score Confirmation

Preserve existing confirmation behavior:

- A player entering their own result automatically confirms that result.
- Results entered for friends remain unconfirmed until confirmed by the appropriate player.
- Dynamically adding or removing participants must not alter these rules.

## 3. Technical Approach

### Django and HTMX

Use HTMX for partial-page updates while keeping all form construction and processing in Django.

The general interaction will be:

1. User selects **Add Another Player** or **Remove**.
2. HTMX submits the current form values to a dedicated endpoint.
3. Django reconstructs the player-result formset with the updated rows.
4. Django renders an HTML partial containing the updated player-result section.
5. HTMX replaces the existing section without refreshing the entire page.

The endpoint must preserve submitted values and remain separate from the final game-saving operation.

### Django Formsets

Continue using the existing `GameResultFormSet` architecture.

- Change the initial number of displayed rows from five to one.
- Retain the five-human-player maximum.
- Support dynamic row addition and deletion.
- Maintain valid Django formset management data.
- Ensure deleted rows are excluded from structural validation and persistence.
- Preserve user-entered values and display validation errors appropriately.

### HTML Templates

Extract the Player Results section into a reusable partial template.

The partial will support both initial page rendering and HTMX updates.

Use the existing Bootstrap styling conventions and HTMX dependency already included in `base.html`.

No additional frontend framework or custom JavaScript should be introduced.

## 4. Files and Responsibilities

| File | Planned changes |
|---|---|
| `portal/forms.py` | Adjust result formset configuration and deletion-aware validation |
| `portal/views/games.py` | Preserve `GameCreateView` and introduce a dedicated HTMX endpoint |
| `portal/templates/portal/game_create.html` | Integrate dynamic player controls and the reusable partial |
| New player-results partial | Render formset rows, controls, errors, and management fields |
| `portal/urls.py` | Register the dedicated HTMX endpoint |
| `portal/services/game_entry.py` | Review compatibility; avoid changing existing business logic unless necessary |
| Tests | Cover dynamic interactions, validation, authorization, and game creation |

## 5. Architectural Constraints

### Preserve Existing Models

The current relationship remains:

- One `Game` has multiple `GameResult` records.
- Each `GameResult` belongs to one `Player`.
- Human player mode remains a property of `Game`.

No database schema changes or migrations are anticipated.

### Preserve Service Responsibilities

`create_game()` remains responsible for:

- Creating the game and its results atomically.
- Enforcing allowed-player restrictions.
- Applying score-confirmation rules.

HTMX endpoints are responsible only for manipulating the form interface.

### Avoid Unnecessary Refactoring

Keep the feature focused on game creation.

The existing Game Edit workflow uses a separate `GameResultEditFormSet`. It should remain functional and unchanged during this initial implementation.

Dynamic player entry for Game Edit may be addressed in a separate feature.

## 6. Potential Implementation Risks

### Formset Management

Django formsets require consistent form indexes and management fields, particularly `TOTAL_FORMS`.

Adding and removing rows must not generate malformed or inconsistent submissions.

### Removing Rows

Deleted rows must not participate in player-count validation, uniqueness checks, or game creation.

The implementation must distinguish between removing an unsaved row and submitting valid participant data.

### HTMX State Preservation

HTMX operations must retain existing player selections, scores, turn orders, game mode, and date.

Partially completed forms should not lose data when another player is added or removed.

### Validation Errors

Invalid submissions must preserve all active rows and entered values.

Row-level and formset-level validation errors must remain visible and understandable.

### Authorization

HTMX endpoints must require authentication and a linked Player.

Player choices must continue to be restricted to the acting player and eligible friends. Client-submitted values must not be trusted as authorization.

### Computer Players

Current formsets represent human player results only.

Future computer-player support may require a separate participant representation or model extension. Avoid embedding assumptions that all future game participants are human.

## 7. Implementation Sequence

1. Update `GameResultFormSet` to support one initial row and dynamic row management.
2. Create the reusable player-results partial template.
3. Implement and register the dedicated HTMX endpoint.
4. Update the Add Game template with Add/Remove controls.
5. Verify value preservation, row limits, and error handling.
6. Test game creation, validation, permissions, and confirmation behavior.
7. Confirm the existing Game Edit workflow remains unaffected.
8. Deploy after successful testing.

## 8. Acceptance Criteria

The feature is complete when:

- The Add Game page initially displays one player-result row.
- Users can dynamically add and remove rows without a full-page refresh.
- Up to five human participants can be entered.
- Existing form values are preserved during HTMX interactions.
- Solo and Competitive game rules remain enforced.
- Invalid submissions show appropriate errors without losing entered data.
- Games and results are saved correctly.
- Friendship permissions and score-confirmation behavior remain unchanged.
- Existing Game Edit functionality continues working.
- No custom JavaScript or database migration is required.

---

**Release principle:** Improve the player-entry experience without changing the underlying game-data architecture, authorization boundaries, or confirmation workflow.