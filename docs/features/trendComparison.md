# Player Trend Comparison

## Purpose

Extend the existing Player Score Trends page so a user can optionally compare a **Primary Player** against a **Secondary Player** over the same game type and time period.

The existing single-player experience should remain available. Selecting a Secondary Player activates comparison mode.

The feature should prioritize mobile usability and direct comparison without duplicating large charts or tables side by side.

---

# Filter Interface

The existing Trends filter should be extended to contain:

- **Primary Player** — required
- **Secondary Player** — optional
- **Game Type** — required
- **Period** — required

The Secondary Player selector should default to a blank option such as:

`No comparison`

The Primary Player and Secondary Player cannot be the same player.

### Display Modes

If no Secondary Player is selected:

- Render the existing single-player Trends experience.

If a Secondary Player is selected:

- Render comparison mode.
- Both players use the same Game Type.
- Both players use the same Period.

The page should continue using GET parameters so both single-player and comparison selections remain bookmarkable and shareable.

---

# Comparison Terminology

Comparison mode should consistently use:

- **P1** — Primary Player
- **P2** — Secondary Player

The Primary Player is the subject of the analysis. The Secondary Player is the comparator.

Charts should reflect this hierarchy:

- P1 uses the stronger foreground treatment.
- P2 uses the lighter background treatment.

Player names may appear in chart legends and contextual labels, but compact tables should use P1 and P2 in their headers.

---

# Monthly Results

The comparison table should use:

`Month | P1 Avg | P2 Avg | Difference | P1 Games | P2 Games | Δ %`

### Calculations

`Difference = P1 Average - P2 Average`

`Δ % = ((P1 Average - P2 Average) / P2 Average) × 100`

P2 is the comparison baseline.

Difference and Δ % should include their sign and display one decimal place where appropriate.

### Month Format

Use abbreviated month and two-digit year:

`Oct ’26`

### Missing Data

If a player has no games during a month:

- Average displays `—`.
- Games displays `0`.
- Difference displays `—`.
- Δ % displays `—`.

Difference and Δ % should only be calculated when both players have results for the month.

---

# Statistical Summary

The comparison table should use:

`Statistic | P1 | P2 | Difference | Δ %`

The table should contain:

- Games Played
- Average Score
- Median Score
- Standard Deviation
- Minimum Score
- 25th Percentile
- 75th Percentile
- 90th Percentile
- Maximum Score

### Calculations

`Difference = P1 - P2`

`Δ % = ((P1 - P2) / P2) × 100`

The existing statistical calculations should remain unchanged. Each player's statistics should be calculated independently and then compared.

Difference values are mathematically neutral. A positive difference means P1 has the larger value; it does not necessarily mean P1 performed better.

For example, a higher Standard Deviation represents greater variability rather than better performance.

Positive and negative differences should therefore not automatically receive success or failure styling.

Unavailable comparison values should display `—`.

---

# Monthly Score Trends

Comparison mode should use a **vertical overlapping bar chart**.

Both players occupy the same x-axis position for each month.

### Primary Player

P1 should:

- Render as the narrower foreground bar.
- Use the stronger visual treatment.
- Display the monthly average above the bar.
- Provide an independent hover/tap tooltip.

### Secondary Player

P2 should:

- Render as the wider background bar.
- Use the lighter visual treatment.
- Not display persistent score labels.
- Provide an independent hover/tap tooltip.

Player 2 should be rendered before Player 1 so the Primary Player remains in the foreground.

### Tooltips

Each player's tooltip should independently show:

- Player identity
- Full month and year
- Average score
- Games played

### Missing Months

Months remain on the shared time axis even when one or both players have no games.

A missing monthly average should produce no bar and should never be represented as zero.

### Axes and Legend

Both players must share the same score axis.

Month labels should use the compact comparison format:

`Oct ’26`

The legend may use the actual player names to clearly associate each player with their visual treatment.

Continuous trend-line overlays should not be added.

---

# Score Distribution

Comparison mode should use **overlapping, density-normalized histograms** with a fitted normal-distribution reference curve for each player.

## Shared Bins

Both players must use identical histogram bins.

The existing 10-point bin width should remain.

The histogram range should cover the combined score range of both players so each score interval represents the same range for P1 and P2.

## Density Normalization

Histogram heights should represent probability density rather than raw game counts.

Each player's histogram should be independently normalized so differences in total games played do not distort the comparison.

The y-axis should therefore represent:

`Density`

The x-axis continues to represent:

`Score`

## Primary Player

P1 should:

- Render as the narrower foreground histogram.
- Use the stronger visual treatment.
- Provide independent hover/tap information.

## Secondary Player

P2 should:

- Render as the wider background histogram.
- Use the lighter visual treatment.
- Provide independent hover/tap information.

## Normal Reference Curves

Both players should retain their own fitted normal curve.

Each curve should be calculated independently using that player's:

- Mean
- Standard deviation

Because the histograms are density-normalized, the normal curves should use probability density directly rather than being scaled according to games played.

The P1 curve should receive the stronger visual treatment and the P2 curve the lighter comparison treatment.

## Histogram Tooltips

Histogram tooltips should favor user-readable information rather than exposing raw density values.

They should include:

- Player identity
- Score range
- Games within the bin
- Percentage of that player's games represented by the bin

---

# Service and View Architecture

Comparison should extend the existing Trends page rather than introduce a separate comparison page or route.

The analytical pipeline should conceptually support:

- One required Primary Player dataset.
- One optional Secondary Player dataset.

Each player's dataset should independently contain the results needed for:

- Monthly score calculations
- Score distribution calculations
- Chart generation

Existing analytical services should remain focused on analyzing a single collection of `GameResult` records.

For example, monthly-score and score-distribution calculations should be called independently for P1 and P2 rather than being rewritten to understand comparison mode.

Comparison-specific logic should combine the resulting analytical data where necessary.

The view should avoid accumulating comparison calculations and presentation logic directly. Comparison preparation should be delegated to appropriate services as the implementation develops.

---

# Chart Architecture

Existing single-player chart behavior should remain intact.

Comparison charts should use explicit comparison chart builders rather than making the existing chart builders responsible for many conditional single-player/comparison behaviors.

This applies to:

- Monthly Score Trends comparison chart
- Score Distribution comparison chart

Both modes may reuse common lower-level helpers where doing so reduces genuine duplication.

---

# Mobile Requirements

Comparison mode should remain usable on typical mobile screens.

The implementation should:

- Avoid placing separate P1 and P2 charts side by side.
- Use overlapping chart series to conserve horizontal space.
- Use compact table headers.
- Avoid unnecessary persistent chart labels.
- Preserve hover/tap access to detailed values.
- Use responsive Bootstrap tables as a fallback when table width exceeds the viewport.
- Keep Plotly charts responsive to their containers.

Mobile usability should be verified during implementation rather than assumed from desktop rendering.

---

# Success Criteria

The feature is complete when:

- A user can view the existing Trends page with only a Primary Player selected.
- A user can optionally select a Secondary Player to activate comparison mode.
- The same player cannot be selected as both Primary and Secondary Player.
- Both players are analyzed using the same Game Type and Period.
- Existing single-player Trends behavior continues to work.
- Monthly Results display both players and their calculated differences.
- Statistical Summary displays both players and their calculated differences.
- Monthly Score Trends use the specified overlapping-bar visualization.
- Score Distribution uses shared-bin, density-normalized overlapping histograms with separate normal curves.
- Missing monthly data is represented correctly without treating missing scores as zero.
- P1 remains the visually dominant player across comparison charts.
- Comparison mode remains readable and usable on mobile devices.
- Existing single-player analytical services are reused rather than duplicated.
- Comparison-specific calculations and chart construction remain separated from core dataset-selection and single-dataset statistical services.
- 
# Implementation Phases

Development should proceed as a series of vertical feature slices rather than implementing the entire comparison service layer before updating the interface.

Each visualization should be taken from service logic through view integration and presentation before moving to the next visualization.

Within each phase, maintain the existing architectural direction:

`service logic → view orchestration → presentation`

The existing single-player Trends functionality should remain operational throughout development.

## Phase 1 — Comparison Foundation

Establish the shared functionality required by all comparison visualizations.

### Form

Update the Trends filter to support:

- Required **Primary Player**
- Optional **Secondary Player**
- Existing Game Type
- Existing Period

The Secondary Player should default to `No comparison`.

Add validation preventing the same player from being selected as both Primary Player and Secondary Player.

### View and Context

Establish the basic distinction between:

- Single-player mode when no Secondary Player is selected.
- Comparison mode when a Secondary Player is selected.

The view should be capable of selecting the appropriate `GameResult` dataset independently for both players using the same Game Type and Period.

No comparison calculations should be performed directly in the view.

At the completion of this phase, selecting a Secondary Player should be supported by the request and context even though the existing visualizations may still display only the Primary Player.

---

## Phase 2 — Monthly Results Comparison

Implement the Monthly Results table as the first complete comparison visualization.

### Service Layer

Add the comparison logic required to:

- Calculate monthly results independently for both players.
- Align both players to the same calendar months.
- Calculate monthly Difference.
- Calculate monthly Δ %.
- Handle months where one or both players have no results.

Existing single-player monthly calculations should be reused rather than duplicated.

### View

Update the view to call the Monthly Results comparison service when a Secondary Player is selected.

### Template

Render the comparison table:

`Month | P1 Avg | P2 Avg | Difference | P1 Games | P2 Games | Δ %`

Single-player mode should continue rendering the existing Monthly Results table.

Verify the completed table on mobile before proceeding.

---

## Phase 3 — Monthly Score Trends Comparison

Implement comparison behavior for the Monthly Score Trends chart.

### Chart Service

Add a dedicated comparison chart builder implementing:

- Shared monthly axis.
- P2 wider background bars.
- P1 narrower foreground bars.
- P1 persistent average-score labels.
- Independent P1 and P2 hover/tap information.
- Correct handling of missing months.
- Shared score axis.
- Responsive Plotly rendering.

The comparison chart should consume the monthly data already established by the previous phase where practical.

The existing single-player chart builder should remain available.

### View and Template

Update the view to select the appropriate single-player or comparison chart builder.

Update the existing chart location in the template to display the resulting chart without duplicating the surrounding page structure.

Verify desktop and mobile rendering before proceeding.

---

## Phase 4 — Statistical Summary Comparison

Implement comparison behavior for the Statistical Summary.

### Service Layer

Add the comparison preparation required to:

- Calculate each player's existing statistical summary independently.
- Align corresponding statistics.
- Calculate Difference.
- Calculate Δ %.
- Handle unavailable comparison values.

Existing score-distribution statistics should remain responsible for analyzing one player's dataset. Comparison logic should operate on the resulting statistics rather than duplicate those calculations.

### View and Template

Update the view to provide the comparison summary when a Secondary Player is selected.

Render:

`Statistic | P1 | P2 | Difference | Δ %`

Single-player mode should continue rendering the existing Statistical Summary.

Verify table readability on mobile before proceeding.

---

## Phase 5 — Score Distribution Comparison

Implement the Score Distribution comparison last because it requires the largest change to the underlying visualization data.

### Distribution Services

Add comparison-specific distribution preparation supporting:

- Combined score range for both players.
- Shared 10-point histogram bins.
- Independent bin counts for each player.
- Independent density normalization.
- Each player's existing mean and standard deviation.
- Data required for two independently fitted normal reference curves.

Existing single-player distribution behavior should remain available.

### Chart Service

Add a dedicated comparison distribution chart builder implementing:

- P2 wider background histogram.
- P1 narrower foreground histogram.
- Shared score bins.
- Shared Density axis.
- P1 and P2 normal reference curves.
- Independent hover/tap information.
- Responsive Plotly rendering.

### View and Template

Update the view to use the comparison distribution services and chart builder when a Secondary Player is selected.

The existing Score Distribution location in the template should render either the single-player or comparison chart as appropriate.

Verify the visualization using players with different:

- Numbers of games.
- Score ranges.
- Means.
- Standard deviations.

---

## Phase 6 — Final Integration and Regression Testing

Once all four comparison visualizations are operational, review the feature as a complete system.

### Refactoring

Remove temporary implementation artifacts introduced during incremental development.

Review:

- View complexity.
- Repeated comparison-mode checks.
- Duplicate context preparation.
- Reusable comparison calculations.
- Shared chart helpers.

Refactor where doing so improves clarity without unnecessarily coupling the single-player and comparison implementations.

### Regression Testing

Verify:

- Existing single-player Trends behavior remains functional.
- Comparison mode activates only when a Secondary Player is selected.
- Primary and Secondary Player validation works.
- Both players always use the same Game Type and Period.
- All four displays switch correctly between single-player and comparison modes.
- Missing monthly data is handled correctly.
- Players with different sample sizes compare correctly.
- Players with different score ranges use valid shared histogram bins.
- Last 12 Months and individual-year periods work correctly.
- Competitive and solo game types work correctly.
- GET parameters remain bookmarkable and shareable.

### Mobile Validation

Perform final testing at typical mobile viewport sizes.

Verify:

- Comparison tables remain readable.
- Horizontal scrolling is minimized and functional where necessary.
- Plotly charts resize correctly.
- Overlapping bars remain distinguishable.
- Chart labels do not create excessive clutter.
- Hover/tap interactions remain usable.
- The complete Trends page maintains a consistent visual hierarchy between the Primary Player and Secondary Player.

The comparison feature is complete when all success criteria defined by this specification are satisfied in both desktop and mobile presentation.