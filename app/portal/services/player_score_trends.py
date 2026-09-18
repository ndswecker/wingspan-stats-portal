from dataclasses import dataclass
from datetime import date, datetime

from django.db.models import Avg, Count, QuerySet
from django.db.models.functions import TruncMonth

from ..models import GameResult


@dataclass(frozen=True)
class MonthlyScoreAverage:
    month_start: date
    month_name: str
    month_abbreviation: str
    average_score: float | None
    games_played: int

@dataclass(frozen=True)
class MonthlyScoreComparison:
    month_start: date

    primary_average_score: float | None
    secondary_average_score: float | None

    difference: float | None
    percentage_difference: float | None

    primary_games_played: int
    secondary_games_played: int

@dataclass(frozen=True)
class ScoreTrendDateRange:
    start_date: date
    end_date: date


def calculate_monthly_score_averages(
    *,
    game_results: QuerySet[GameResult],
    start_date: date,
    end_date: date,
) -> list[MonthlyScoreAverage]:
    """
    Calculate average score and games played for each month in a date range.

    The returned list contains one entry for every calendar month in the
    requested range. Months without game results use an average score of None
    and a games-played count of zero.
    """

    if start_date > end_date:
        raise ValueError("start_date cannot be later than end_date.")

    month_starts = _build_month_starts(
        start_date=start_date,
        end_date=end_date,
    )

    aggregated_results = (
        game_results
        .annotate(
            month=TruncMonth("game__date_played"),
        )
        .values("month")
        .annotate(
            average_score=Avg("score"),
            games_played=Count("id"),
        )
        .order_by("month")
    )

    results_by_month = {
        _normalize_month_value(result["month"]): result
        for result in aggregated_results
    }

    return [
        _build_monthly_score_average(
            month_start=month_start,
            aggregated_result=results_by_month.get(month_start),
        )
        for month_start in month_starts
    ]


def _build_month_starts(
    *,
    start_date: date,
    end_date: date,
) -> list[date]:
    current_month = start_date.replace(day=1)
    final_month = end_date.replace(day=1)

    month_starts = []

    while current_month <= final_month:
        month_starts.append(current_month)
        current_month = _get_next_month(current_month)

    return month_starts


def _get_next_month(month_start: date) -> date:
    if month_start.month == 12:
        return date(month_start.year + 1, 1, 1)

    return date(
        month_start.year,
        month_start.month + 1,
        1,
    )


def _normalize_month_value(value: date | datetime) -> date:
    if isinstance(value, datetime):
        value = value.date()

    return value.replace(day=1)


def _build_monthly_score_average(
    *,
    month_start: date,
    aggregated_result: dict | None,
) -> MonthlyScoreAverage:
    if aggregated_result is None:
        return MonthlyScoreAverage(
            month_start=month_start,
            month_name=month_start.strftime("%B"),
            month_abbreviation=month_start.strftime("%b"),
            average_score=None,
            games_played=0,
        )

    return MonthlyScoreAverage(
        month_start=month_start,
        month_name=month_start.strftime("%B"),
        month_abbreviation=month_start.strftime("%b"),
        average_score=float(aggregated_result["average_score"]),
        games_played=aggregated_result["games_played"],
    )

def compare_monthly_score_averages(
    *,
    primary_monthly_scores: list[MonthlyScoreAverage],
    secondary_monthly_scores: list[MonthlyScoreAverage],
) -> list[MonthlyScoreComparison]:
    if len(primary_monthly_scores) != len(secondary_monthly_scores):
        raise ValueError(
            "Primary and secondary monthly score lists must cover the same period."
        )

    comparisons = []

    for primary_score, secondary_score in zip(
        primary_monthly_scores,
        secondary_monthly_scores,
    ):
        if primary_score.month_start != secondary_score.month_start:
            raise ValueError(
                "Primary and secondary monthly scores must contain matching months."
            )

        difference = None
        percentage_difference = None

        if (
            primary_score.average_score is not None
            and secondary_score.average_score is not None
        ):
            difference = (
                primary_score.average_score - secondary_score.average_score
            )

            if secondary_score.average_score != 0:
                percentage_difference = (
                    difference / secondary_score.average_score * 100
                )

        comparisons.append(
            MonthlyScoreComparison(
                month_start=primary_score.month_start,
                primary_average_score=primary_score.average_score,
                secondary_average_score=secondary_score.average_score,
                difference=difference,
                percentage_difference=percentage_difference,
                primary_games_played=primary_score.games_played,
                secondary_games_played=secondary_score.games_played,
            )
        )

    return comparisons

def resolve_score_trend_date_range(
    *,
    primary_game_results: QuerySet[GameResult],
    secondary_game_results: QuerySet[GameResult] | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> ScoreTrendDateRange:
    """
    Resolve concrete date boundaries for score-trend calculations,
    
    Explicit date boundaries are preserved. Missing boundaries are derived
    from available game results. When comparison results are provided, the
    resolved range covers the complete span of both datasets.
    """

    if not primary_game_results.exists():
        raise ValueError("Primary game results are required to resolve a score-trend date range.")

    if start_date is None:
        earliest_dates = [
            primary_game_results.earliest("game__date_played").game.date_played,
        ]

        if secondary_game_results is not None and secondary_game_results.exists():
            earliest_dates.append(
                secondary_game_results.earliest("game__date_played").game.date_played,
            )

        start_date = min(earliest_dates)

    if end_date is None:
        latest_dates = [
            primary_game_results.latest("game__date_played").game.date_played,
        ]

        if secondary_game_results is not None and secondary_game_results.exists():
            latest_dates.append(
                secondary_game_results.latest("game__date_played").game.date_played,
            )

        end_date = max(latest_dates)

    if start_date > end_date:
        raise ValueError("start_date cannot be later than end_date.")

    return ScoreTrendDateRange(
        start_date=start_date,
        end_date=end_date,
    )