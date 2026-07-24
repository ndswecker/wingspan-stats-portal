# Staff Game Entry Requirements

## Purpose

Provide a staff-only web interface for recording completed Wingspan games without requiring direct access to the Django Admin or the CSV importer.

This page is intended to become the primary method of entering new games into the application.

The existing CSV importer remains a destructive bootstrap utility used only for initial database population.

---

# Access Control

## Authentication

The page requires an authenticated Django user.

Unauthenticated users are redirected to the login page.

## Authorization

Only users with `is_staff=True` may access this page.

Authenticated users without staff privileges receive an HTTP 403 response.

## Navigation

A navigation link to the page should only be visible to staff users.

Server-side authorization must always be enforced regardless of whether the navigation link is visible.

---

# User Interface

The page consists of a single game submission form.

The form contains two sections:

## Game Information

- Date Played
- Human Player Mode

## Player Results

The form always displays **five player rows**.

Each row contains:

- Player dropdown
- Score input
- Turn Order input

Rows are never dynamically added or removed.

Unused rows remain blank.

---

# Game Information

## Date Played

Requirements:

- Required field
- HTML date input
- Defaults to today's date
- Future dates are not permitted

## Human Player Mode

The user selects one of the existing model values:

- Solo Game
- Competitive Game

The form displays the human-readable labels rather than the stored database values.

---

# Player Result Rows

Each visible row represents one potential `GameResult`.

Each row contains:

## Player

- Dropdown of active players
- Required only if the row is used
- A player may only appear once within a submitted game

Inactive players remain associated with historical games but are not selectable for new games.

Player creation is outside the scope of this feature.

---

## Score

- Integer input
- Required if a player is selected
- Must be zero or greater

---

## Turn Order

- Integer input
- Required if a player is selected
- Must be a positive integer
- No two submitted players may share the same turn order

Although the expected values are normally between 1 and 5, the application only requires that submitted values are positive and unique.

The user is responsible for entering the desired turn order.

---

# Blank Row Behavior

A row is ignored only when all fields are empty.

A row containing:

- Player
- Score
- Turn Order

must contain all three values.

Examples:

| Player | Score | Turn Order | Result |
|---------|------:|-----------:|--------|
| blank | blank | blank | Ignored |
| Nate | 108 | 1 | Saved |
| Nate | blank | 1 | Validation Error |
| blank | 108 | 1 | Validation Error |
| Nate | 108 | blank | Validation Error |

---

# Solo Game Rules

When the game mode is **Solo Game**:

- Exactly one player row must be completed.
- The remaining rows remain blank.

Submitting more than one player for a solo game is invalid.

---

# Competitive Game Rules

When the game mode is **Competitive Game**:

- At least two player rows must be completed.
- Up to five player rows may be completed.

The interface always displays five rows regardless of game type.

---

# Validation Rules

The application validates the complete submission before saving.

## Game Validation

- Date is present
- Date is not in the future
- Human Player Mode is valid

## Player Validation

For every populated row:

- Player is selected
- Score is entered
- Turn Order is entered
- Score is zero or greater
- Turn Order is a positive integer

## Cross-Row Validation

- Players may not be duplicated
- Turn Orders may not be duplicated

## Mode Validation

Solo Game

- Exactly one populated player row

Competitive Game

- Minimum of two populated player rows
- Maximum of five populated player rows

---

# Database Persistence

A successful submission creates:

- One `Game`
- One `GameResult` for each populated player row

The entire operation must execute inside a single database transaction.

If any validation or save operation fails:

- No Game is created
- No GameResults are created

Partial saves are not permitted.

---

# Successful Submission

After successfully saving:

- Display a success message.
- Redirect using the POST/Redirect/GET pattern.
- Allow the user to immediately enter another game.

---

# Out of Scope

The following features are intentionally excluded from the initial implementation:

- Editing existing games
- Deleting games
- Creating new players
- Editing players
- Recording Automa information
- Recording expansions
- Recording bird selections
- Recording bonus cards
- Duplicate game detection

These features may be implemented in future iterations.

---

# Security Requirements

The implementation must:

- Require CSRF protection
- Require authenticated staff users
- Validate all business rules server-side
- Reject inactive players
- Reject invalid player IDs
- Never trust client-side validation alone

---

# Technical Design

The implementation should follow Django best practices.

Recommended components:

- `GameCreateView`
- `GameForm`
- `GameResultForm`
- Fixed-size `GameResultFormSet` containing five forms
- Service layer responsible for transactional game creation

The service layer should own the business logic and persistence while the view remains responsible for HTTP concerns.

---

# Acceptance Criteria

The feature is complete when:

1. Only authenticated staff users may access the page.
2. The page displays one Game form and five Player Result rows.
3. Blank player rows are ignored.
4. Partially completed rows generate validation errors.
5. Solo games require exactly one populated player row.
6. Competitive games require between two and five populated player rows.
7. Duplicate players are rejected.
8. Duplicate turn orders are rejected.
9. Successful submissions create one Game and the expected GameResult records.
10. Failed submissions create no database records.
11. Validation errors preserve previously entered values.
12. A successful submission redirects with a confirmation message.
13. The page is responsive and usable on desktop and mobile devices.