# Individual Player Statistics

## Purpose

Introduce the first player-focused statistics page to the Wingspan Stats Portal while establishing the architectural foundation for future analytical features.

The initial page will allow a user to select a player and view basic score statistics. Although the first implementation is intentionally small, the supporting architecture should be designed so that it can grow naturally into more advanced analytical capabilities without requiring significant redesign.

This feature serves as the first consumer of a reusable Game Result Selection System.

---

# User Feature

The first visible feature is **Individual Player Statistics**.

The page will allow the user to:

* Select a player.
* Select a game type.
* View summary statistics for the selected data set.

The initial statistics will include:

* Average score
* Minimum score
* Maximum score

Future iterations may add additional statistics, charts, comparisons, and filtering options.

---

# Architectural Goal

This feature introduces a reusable **Game Result Selection System**.

The purpose of this system is to provide a consistent mechanism for selecting collections of `GameResult` records for analytical purposes throughout the application.

The Individual Player Statistics page is simply the first consumer of this system.

Future consumers may include:

* Dashboard widgets
* Player profile pages
* Multiplayer comparisons
* Monthly reports
* Charts and visualizations
* Data exports

---

# Responsibilities

## Game Result Selection System

The Game Result Selection System is responsible only for selecting the appropriate collection of `GameResult` records.

It answers one question:

> Which `GameResult` records satisfy the supplied selection criteria?

The selection system is **not** responsible for:

* Calculating statistics
* Building presentation models
* Preparing template context
* Rendering charts
* Determining rankings

Its only responsibility is dataset selection.

---

## Statistics Services

Separate analytical services consume the selected `GameResult` collection.

Examples include:

* Average score
* Minimum score
* Maximum score
* Win percentage
* Trends
* Histograms
* Future analytical calculations

Statistics services should not determine which records belong in the dataset. They operate only on the selected collection they receive.

---

# Primary Domain Object

The primary domain object for analytical selection is `GameResult`.

Statistics are fundamentally based on individual player results, not directly on `Game` or `Player` objects.

Games, players, dates, and other attributes exist primarily as selection criteria that determine which `GameResult` records belong in the analytical dataset.

---

# Incremental Development Philosophy

The Game Result Selection System should be developed incrementally.

Each iteration should introduce one additional selection capability while preserving a clean architectural boundary between selection and analysis.

The initial implementation should support:

* One player
* Competitive games
* All recorded dates

Future iterations may expand the selection system to support:

* Multiple players
* Additional game types
* Date ranges
* Explicit game selection
* Additional selection criteria as real application requirements emerge

Generalization should be driven by actual feature needs rather than anticipated complexity.

---

# Design Principles

The implementation should continue the architectural conventions established throughout the project:

* Thin Django views
* Business logic in service modules
* Explicit and readable code
* Incremental development
* Composable services
* Minimal unnecessary abstraction
* Separate dataset selection from statistical analysis

Implementation details such as request objects or DTOs may be introduced in future iterations if they become beneficial through repeated usage patterns, but they are intentionally outside the scope of this specification.

---

# Initial Implementation Scope

The first implementation should establish the architectural pattern while remaining intentionally small.

The page will:

* Allow selection of one player.
* Allow selection of game type.
* Select the appropriate `GameResult` records.
* Calculate average, minimum, and maximum score.
* Display those values to the user.

This implementation serves as the foundation upon which future analytical capabilities will be built.
