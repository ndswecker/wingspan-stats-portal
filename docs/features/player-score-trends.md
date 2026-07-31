
# Player Score Trends

## Purpose

The Player Score Trends page provides a focused analytical view of a single player's scoring performance over a selected twelve-month period.

Rather than presenting isolated charts, the page analyzes a single filtered collection of `GameResult` records and presents multiple complementary views of the same dataset.

The page should help answer questions such as:

- How has the player's average score changed over time?
- Which months were strongest or weakest?
- How consistent are the player's scores?
- What score range occurs most frequently?
- How unusual are exceptionally high or low scores?

Every visualization and statistic on the page must represent the same filtered dataset.

---

# Page Location

Route:

```text
/players/score-trends/
```

Recommended names:

```python
view: player_score_trends
url name: player-score-trends
template: player_score_trends.html
```

---

# Architectural Overview

```text
User Selection
        │
        ▼
Game Result Selection
        │
        ▼
Player Analysis
    ├── Trend Analysis
    └── Distribution Analysis
        │
        ▼
Presentation
```

---

# Filters

The page contains a GET form with:

- Player
- Game Type
- Period
- Submit button

These filters produce one filtered collection of `GameResult` records. Every analytical service consumes this same collection.

---

# Period Definitions

## Calendar Year

Displays January through December of the selected year.

Exactly twelve monthly buckets are returned.

## Last 12 Months

Displays the rolling twelve-month period ending with the current month.

This period advances automatically as time passes.

---

# Responsibilities

## Game Result Selection

Responsible for:

- selecting `GameResult` records

Not responsible for:

- statistics
- chart generation
- presentation

---

## Trend Analysis

Responsible for:

- monthly aggregation
- monthly averages
- monthly game counts

Not responsible for:

- chart generation

---

## Distribution Analysis

Responsible for:

- histogram bins
- descriptive statistics
- percentile calculations
- fitted normal distribution values

Not responsible for:

- chart generation

---

## Chart Builders

Responsible only for constructing chart objects from already-calculated analytical data.

Chart builders must not:

- query the database
- calculate statistics

---

# Trend Analysis

Continue using:

```python
resolve_score_trend_period()
calculate_monthly_score_averages()
build_monthly_score_chart()
```

The trend analysis displays:

- Monthly average score chart
- Monthly results table

The monthly table remains the authoritative numerical representation of the trend chart.

---

# Distribution Analysis

Introduce:

```python
calculate_score_distribution()
build_score_distribution_chart()
```

The statistical service returns a dedicated domain model.

```python
@dataclass(frozen=True)
class HistogramBin:
    lower_bound: int
    upper_bound: int
    games_played: int


@dataclass(frozen=True)
class NormalCurvePoint:
    score: float
    density: float


@dataclass(frozen=True)
class ScoreDistribution:
    games_played: int

    average_score: float
    median_score: float
    standard_deviation: float

    minimum_score: int
    percentile_25: float
    percentile_75: float
    percentile_90: float
    maximum_score: int

    histogram_bins: list[HistogramBin]
    normal_curve_points: list[NormalCurvePoint]
```

---

# Histogram Design

The histogram uses exactly the same filtered dataset as the monthly trend chart.

Recommended binning strategy:

- Fixed-width bins
- Five-point score intervals
- Inclusive lower bound
- Exclusive upper bound
- Automatically expand to contain the entire observed score range

This keeps histograms visually comparable across players and periods.

---

# Normal Distribution Reference

The fitted normal distribution exists only as a visual comparison against the observed score distribution.

It is **not** intended to imply that Wingspan scores are normally distributed.

The curve is calculated from:

- sample mean
- sample standard deviation

The histogram remains the authoritative representation of the underlying data.

---

# Presentation

The completed page contains:

1. Filter controls
2. Monthly trend chart
3. Score distribution histogram
4. Statistical summary
5. Monthly results table

All components visualize the same filtered `GameResult` collection.

---

# Page States

## Initial

Display:

- filter form
- instructional message

No charts are shown.

## No Results

Display a message indicating that no matching games were found.

No charts are rendered.

## Populated

Display:

- trend chart
- histogram
- statistics
- monthly table

---

# Design Principles

- Thin Django views
- Business logic in services
- One reusable dataset selection service
- Independent analytical services
- Independent chart builders
- Explicit domain models
- Incremental development
- Separation of data retrieval, analysis, and presentation

---

# Future Expansion

Future analytical modules may consume the same selected `GameResult` collection.

Examples include:

- Win probability
- Rolling averages
- Personal best tracking
- Opponent comparisons
- Score breakdowns
- Achievement tracking

---

# Implementation Phases

## Phase 1 — Selection

- Shared filter form
- Result selection
- Period resolution

## Phase 2 — Trend Analysis

- Monthly aggregation
- Monthly table
- Trend chart

## Phase 3 — Distribution Analysis

- Summary statistics
- Percentiles
- Histogram bins
- Normal curve values

## Phase 4 — Visualization

- Histogram
- Statistical summary

## Phase 5 — Integration

- Responsive layout
- Shared page behavior

## Phase 6 — Validation

Verify:

- dataset selection
- monthly aggregation
- histogram frequencies
- statistical calculations
- percentile calculations
- responsive behavior

---

# Completion Criteria

The feature is complete when:

- shared filters drive every analytical component
- every visualization represents the same filtered dataset
- trend analysis is accurate
- distribution analysis is accurate
- chart builders contain no business logic
- analytical services perform no presentation logic
- the page functions correctly on desktop and mobile
