from dataclasses import dataclass
from datetime import date

from ..models import Player

from .player_game_results import (
    PlayerDailyResult,
    PlayerHistorySummary,
    build_player_history_with_summary,
)


@dataclass(frozen=True)
class PlayerHistoryComparisonRow:
    date_played: date
    primary_daily_result: PlayerDailyResult | None
    secondary_daily_result: PlayerDailyResult | None

@dataclass(frozen=True)
class PlayerHistoryComparison:
    primary_summary: PlayerHistorySummary
    secondary_summary: PlayerHistorySummary
    rows: list[PlayerHistoryComparisonRow]

def align_player_histories(
    *,
    primary_history: list[PlayerDailyResult],
    secondary_history: list[PlayerDailyResult],
) -> list[PlayerHistoryComparisonRow]:
    """
    Align two player histories using the union of their game dates.
    """

    # Index each player's history by date. This changes the history from a list into
    # a dictionary where the date is the key
    primary_results_by_date = {
        daily_result.date_played: daily_result
        for daily_result in primary_history
    }
    secondary_results_by_date = {
        daily_result.date_played: daily_result
        for daily_result in secondary_history
    }

    # Build the union of dates. Ensure each date appears only once, 
    # and add the secondary player's dates
    comparison_dates = set(primary_results_by_date.keys())
    comparison_dates.update(secondary_results_by_date.keys())

    # Sort newest dates first
    sorted_dates = sorted(
        comparison_dates,
        reverse=True,
    )

    # Build one comparison row per date
    comparison_rows = []

    for date_played in sorted_dates:
        comparison_row = PlayerHistoryComparisonRow(
            date_played=date_played,
            primary_daily_result=primary_results_by_date.get(date_played),
            secondary_daily_result=secondary_results_by_date.get(date_played),
        )

        comparison_rows.append(comparison_row)

    return comparison_rows

def build_player_history_comparison(
    *,
    primary_player: Player,
    secondary_player: Player,
    start_date: date | None = None,
    end_date: date | None = None,
) -> PlayerHistoryComparison:
    """
    Build two players' competitive histories, summaries,
    and aligned comparison rows.
    """

    primary_history = build_player_history_with_summary(
        player=primary_player,
        start_date=start_date,
        end_date=end_date,
    )

    secondary_history = build_player_history_with_summary(
        player=secondary_player,
        start_date=start_date,
        end_date=end_date,
    )

    comparison_rows = align_player_histories(
        primary_history=primary_history.daily_results,
        secondary_history=secondary_history.daily_results,
    )

    return PlayerHistoryComparison(
        primary_summary=primary_history.summary,
        secondary_summary=secondary_history.summary,
        rows=comparison_rows,
    )