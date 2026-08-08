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