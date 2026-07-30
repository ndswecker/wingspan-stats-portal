# Player Score Trends

## Purpose

Create a page that shows one player's average score by month for a selected calendar year.

The feature should help answer:

* How did the player's average score change during the year?
* Which months had the highest and lowest averages?
* How many games contributed to each monthly average?

---

## Page Location

Create a separate page rather than adding more content to Player Overview.

Recommended route:

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

## Filters

The page will use a GET form with:

* Player
* Game type
* Period
* Submit button

Only one player, one game type, and one period may be selected at a time.

## Period Definitions

The selected period determines the date range used during aggregation.

### Calendar Year

Selecting a year displays the full calendar year Example:
```
2026

January 2026
through
December 2026
```
The chart always displays twelve months.

### Last 12 Months
Selecting the Last 12 Months displays the most recent twleve monthly buckets ending with the current month. 

For example, if today is July 29, 2026, the chart displays:
```August 2025
through
July 2026
```
This period automatically advances as time passes.
---

## Chart

Use Plotly to create a responsive vertical column chart.

The chart shall display:

  * one column per populated month;
  * average score on the vertical axis;
  * chronological months on the horizontal axis.

The chart must remain a vertical column chart on both desktop and mobile.

The axes should never rotate based on screen size.

For missing months:

```python
average_score = None
games_played = 0
```

Missing months should not be represented as zero. No column should appear for missing months.

Tooltips should show:

```text
March 2026
Average score: 88.3
Games played: 5
```

The legend should be hidden because there is only one data series.

---

## Mobile Requirements

The chart must remain a vertical column chart on mobile.

Plotly should be configured responsively so the chart:

* uses the full available width;
* does not create page-level horizontal scrolling;
* keeps abbreviated month labels;
* remains usable on screens around 320 pixels wide;
* provides touch-friendly tooltips.

The chart may use a taller height on mobile if needed.

---

## Monthly Data Table

Display a table beneath the chart using the same monthly dataset.

Required columns:

| Month | Average Score | Games Played |
| ----- | ------------: | -----------: |

All twelve months should appear.

Months without games should display:

```text
No games
```

The table provides exact values and a usable fallback for viewers who cannot interact with the chart.

---

## Service Design

Reuse the existing result-selection service:

```python
select_game_results(
    player=player,
    game_type=game_type,
)
```

Instead of passing a year into the aggregation service, pass a resolved date range:
```python
calculate_monthly_score_averages(
    game_results=game_results,
    start_date=start_date,
    end_date=end_date,
)
```

The aggregation service should:

1. Filter results to the supplied date range.
2. Group results by month.
3. Calculate average score.
4. Count games played.
5. Return twelve monthly buckets.
6. Fill missing months with None and zero games.

The database should handle grouping, averaging, and counting.

Python should only fill in the missing months.

Likely Django ORM tools:

```python
TruncMonth
Avg
Count
```

---

## Period Resolution

Use a small helper to convert the selected period into a date range.

Recommended function:

```python
resolve_score_trend_period(
    selected_period=selected_period,
)
```

Example results:
```python
"2026"
# 2026-01-01 through 2026-12-31
```
```
"last_12_months"
# First day of the month eleven months ago
# through the last day of the current month
```

This keeps date-range logic separate from aggregation and makes future periods easier to add.

---

## Return Structure

Use a small dataclass for the monthly results.

```python
@dataclass(frozen=True)
class MonthlyScoreAverage:
    month_start: date
    month_name: str
    month_abbreviation: str
    average_score: float | None
    games_played: int
```

The aggregation service should return:

```python
list[MonthlyScoreAverage]
```

Using `month_start` rather than only `month_number` is important because the Last 12 Months period can span two calendar years.

---

## Plotly Builder

Keep Plotly construction separate from database aggregation.

Recommended function:

```python
build_monthly_score_chart(
    monthly_scores=monthly_scores,
    player=selected_player,
    game_type_label=selected_game_type_label,
    period_label=selected_period_label,
)
```

The builder should:

  * create the Plotly column chart;
  * configure chronological month ordering;
  * configure tooltips;
  * hide the legend;
  * apply responsive settings.

It should not query the database.

For calendar-year views, labels may use:
```text
Jan
Feb
Mar
...
```

For Last 12 Months, labels should include the year to avoid ambiguity:

```text
Aug 25
Sep 25
...
Jan 26
...
Jul 26
```
---

## Page States

### Initial state

Display:
  * the filter form;
  * an instructional message.

```text
Select a player, game type, and period to view monthly score trends.
```

Do not show an empty chart.

### No results

Show:

```text
No matching games were found for this selection.
```

Do not show an empty Plotly chart.

### Partial Data

Show all twelve months.

Only months with data should display columns.

---

## Implementation Sequence

### Phase 1: Monthly Aggregation

1. Create `MonthlyScoreAverage`.
2. Implement date-range-based monthly aggregation.
3. Normalize the result to twelve months.
4. Verify results manually against existing game data.

### Phase 2: Period Selection

1. Create the player, game-type, and period form.
2. Populate available calendar years.
3. Add the 'Last 12 Months' option.
4. Implement `resolve_score_trend_period()`.
5. Confirm GET parameters work correctly.

### Phase 3: Plotly

1. Add Plotly to the project dependencies (probably alread done).
2. Create the chart-building function.
3. Configure responsive behavior and tooltips.
4. Confirm missing months remain empty.

### Phase 4: Page

1. Add the URL and view.
2. Add the template.
3. Display the chart.
4. Add the monthly table.
5. Add initial and no-data states.

### Phase 5: User Testing

Manually verify:

* correct monthly averages;
* correct game counts;
* correct period filtering;
* correct game-type filtering;
* missing-month behavior;
* desktop layout;
* mobile layout;
* touch tooltips;
* no unintended horizontal scrolling.

---

## Completion Criteria

The feature is complete when:

  * one player can be selected;
  * one game type can be selected;
  * one period can be selected;
  * both calendar-year and Last 12 Months periods work correctly;
  * every period displays exactly twelve monthly buckets;
  * monthly averages are correct;
  * monthly game counts are correct;
  * missing months use None, not zero;
  * the Plotly chart remains a responsive vertical column chart;
  * tooltips display average score and games played;
  * the monthly table matches the chart;
  * the feature works on desktop and mobile.
