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
        .filter(
            game__date_played__range=(start_date, end_date),
        )
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