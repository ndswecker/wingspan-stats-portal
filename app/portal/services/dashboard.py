from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from django.db.models import Count, Avg

from ..models import Game, GameResult, Player
from ..types import PlayerPerformanceSummary

def get_total_games_played():
    """Returns the total number of games played."""
    return Game.objects.count()

def get_player_performance_summary() -> list[PlayerPerformanceSummary]:
    players = list(Player.objects.filter(is_active=True).order_by("name"))

    games_played_by_player = {}
    average_score_by_player = {}

    result_stats = (
        GameResult.objects
        .values("player_id")
        .annotate(
            games_played=Count("id"),
            average_score=Avg("score"),
        )
    )

    for stat in result_stats:
        player_id = stat["player_id"]
        games_played_by_player[player_id] = stat["games_played"]
        average_score_by_player[player_id] = _round_average(stat["average_score"])

    game_wins_by_player = defaultdict(int)
    night_wins_by_player = defaultdict(int)

    games = (
        Game.objects
        .prefetch_related("results__player")
        .order_by("date_played", "id")
    )

    night_summary = defaultdict(lambda: {
        "game_wins": defaultdict(int),
        "total_points": defaultdict(int),
    })

    for game in games:
        results = list(game.results.all())

        if len(results) != 2:
            continue

        for result in results:
            night_summary[game.date_played]["total_points"][result.player_id] += result.score

        winner = _get_game_winner(results)

        if winner is not None:
            game_wins_by_player[winner.player_id] += 1
            night_summary[game.date_played]["game_wins"][winner.player_id] += 1

    for stats in night_summary.values():
        night_winner_player_id = _get_night_winner_player_id(stats)

        if night_winner_player_id is not None:
            night_wins_by_player[night_winner_player_id] += 1

    return [
        PlayerPerformanceSummary(
            player=player,
            games_played=games_played_by_player.get(player.id, 0),
            game_wins=game_wins_by_player[player.id],
            night_wins=night_wins_by_player[player.id],
            average_score=average_score_by_player.get(player.id),
        )
        for player in players
    ]


def _get_game_winner(results):
    first_result = results[0]
    second_result = results[1]

    if first_result.score > second_result.score:
        return first_result

    if second_result.score > first_result.score:
        return second_result

    return None


def _get_night_winner_player_id(stats):
    player_ids = list(stats["total_points"].keys())

    if len(player_ids) != 2:
        return None

    first_player_id = player_ids[0]
    second_player_id = player_ids[1]

    first_game_wins = stats["game_wins"][first_player_id]
    second_game_wins = stats["game_wins"][second_player_id]

    if first_game_wins > second_game_wins:
        return first_player_id

    if second_game_wins > first_game_wins:
        return second_player_id

    first_total_points = stats["total_points"][first_player_id]
    second_total_points = stats["total_points"][second_player_id]

    if first_total_points > second_total_points:
        return first_player_id

    if second_total_points > first_total_points:
        return second_player_id

    return None


def _round_average(value):
    if value is None:
        return None

    return Decimal(str(value)).quantize(
        Decimal("0.1"),
        rounding=ROUND_HALF_UP,
    )