
from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from collections import defaultdict

from django.db.models import QuerySet

from ..models import Game, Player

class GameOutcome(StrEnum):
    WIN = "win"
    LOSS = "loss"
    TIE = "tie"

@dataclass(frozen=True)
class PlayerGameResult:
    game: Game
    player: Player
    score: int
    outcome: GameOutcome

@dataclass(frozen=True)
class PlayerDailyResult:
    player: Player
    date_played: date
    game_results: list[PlayerGameResult]
    games_played: int
    wins: int
    losses: int
    ties: int
    total_score: int

def select_player_competitive_games(
    *,
    player: Player,
    start_date: date | None = None,
    end_date: date | None = None,
) -> QuerySet[Game]:
    """
    Select competitive games in which the player participated.

    Related game results and players are prefetched for downstream outcome
    calculations. Optional date bounds are inclusive.
    """
    if start_date is not None and end_date is not None and start_date > end_date:
        raise ValueError("start_date cannot be later than end_date.")

    games = (
        Game.objects
        .filter(
            human_player_mode=Game.HumanPlayerMode.MULTIPLE,
            results__player=player,
        )
        .prefetch_related("results__player")
        .order_by("-date_played", "-id")
    )

    if start_date is not None:
        games = games.filter(date_played__gte=start_date)

    if end_date is not None:
        games = games.filter(date_played__lte=end_date)

    return games

def calculate_player_game_result(
    *,
    game: Game,
    player: Player,
) -> PlayerGameResult:
    """
    Calculate the selected player's outcome for one competitive game.
    """
    if game.human_player_mode != Game.HumanPlayerMode.MULTIPLE:
        raise ValueError(
            "Player game results can only be calculated for competitive games."
        )

    game_results = list(game.results.all())

    player_result = None

    for result in game_results:
        if result.player_id == player.id:
            player_result = result
            break

    if player_result is None:
        raise ValueError(
            "The selected player did not participate in this game."
        )

    highest_score = max(
        result.score
        for result in game_results
    )

    if player_result.score < highest_score:
        outcome = GameOutcome.LOSS

    else:
        highest_score_count = sum(
            1
            for result in game_results
            if result.score == highest_score
        )

        if highest_score_count > 1:
            outcome = GameOutcome.TIE
        else:
            outcome = GameOutcome.WIN

    return PlayerGameResult(
        game=game,
        player=player,
        score=player_result.score,
        outcome=outcome,
    )

def build_player_game_results(
    *,
    games: QuerySet[Game],
    player: Player,
) -> list[PlayerGameResult]:
    """
    Builds the selected player's result for each competitive game.
    """
    player_game_results = []

    for game in games:
        player_game_result = calculate_player_game_result(
            game=game,
            player=player,
        )

        player_game_results.append(player_game_result)

    return player_game_results

from collections import defaultdict


def group_player_game_results_by_date(
    *,
    player_game_results: list[PlayerGameResult],
) -> dict[date, list[PlayerGameResult]]:
    """
    Group a player's calculated game results by the date each game was played.
    """
    results_by_date = defaultdict(list)

    for player_game_result in player_game_results:
        date_played = player_game_result.game.date_played

        results_by_date[date_played].append(
            player_game_result,
        )

    return dict(results_by_date)

def calculate_player_daily_result(
    *,
    player: Player,
    date_played: date,
    player_game_results: list[PlayerGameResult],
) -> PlayerDailyResult:
    """Calculate one player's aggregate competitive results for one date"""

    wins = 0
    losses = 0
    ties = 0
    total_score = 0

    for player_game_result in player_game_results:
        if player_game_result.player != player:
            raise ValueError("All game results must belong to the selected player")

        if player_game_result.game.date_played != date_played:
            raise ValueError("All game results must belong to the selected date")

        total_score += player_game_result.score

        if player_game_result.outcome == GameOutcome.WIN:
            wins += 1
        elif player_game_result.outcome == GameOutcome.LOSS:
            losses += 1
        elif player_game_result.outcome == GameOutcome.TIE:
            ties += 1

    return PlayerDailyResult(
        player=player,
        date_played=date_played,
        game_results=player_game_results,
        games_played=len(player_game_results),
        wins=wins,
        losses=losses,
        ties=ties,
        total_score=total_score,
    )

def build_player_daily_results(
    *,
    player: Player,
    grouped_player_game_results: dict[date, list[PlayerGameResult]],
) -> list[PlayerDailyResult]:
    """Build the player's daily results from game results grouped by date"""

    player_daily_results = []

    for date_played, player_game_results in grouped_player_game_results.items():
        player_daily_result = calculate_player_daily_result(
            player=player,
            date_played=date_played,
            player_game_results=player_game_results,
        )

        player_daily_results.append(player_daily_result)

    player_daily_results.sort(
        key=lambda daily_result: daily_result.date_played,
        reverse=True,
    )

    return player_daily_results

def build_player_history(
    *,
    player: Player,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[PlayerDailyResult]:
    """Build a player's competitive game history grouped into daily results."""

    # Select all competitive games involving the player within the requested date range.
    games = select_player_competitive_games(
        player=player,
        start_date=start_date,
        end_date=end_date,
    )

    # Convert each selected game into a PlayerGameResult
    # This is where the player's WIN, LOSS, or TIE outcome is determined.
    player_game_results = build_player_game_results(
        games=games,
        player=player,
    )

    # Organize the individual game results by the date each game was played.
    grouped_player_game_results = group_player_game_results_by_date(
        player_game_results=player_game_results,
    )

    # Build one PlayerDailyResult for each date, including daily totals
    # and the individual game results for that day.
    player_daily_results = build_player_daily_results(
        player=player,
        grouped_player_game_results=grouped_player_game_results,
    )

    return player_daily_results
