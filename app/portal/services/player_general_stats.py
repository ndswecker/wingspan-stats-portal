from django.db.models import Avg, Min, Max, Count, QuerySet

from ..models import GameResult

def calculate_general_stats(
    *,
    game_results: QuerySet[GameResult],
) -> dict:
    general_stats = game_results.aggregate(
        average_score = Avg("score"),
        minimum_score = Min("score"),
        maximum_score = Max("score"),
        games_played = Count("id"),
    )

    return general_stats