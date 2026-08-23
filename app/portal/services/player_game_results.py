
from dataclasses import dataclass
from datetime import date
from enum import StrEnum

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

