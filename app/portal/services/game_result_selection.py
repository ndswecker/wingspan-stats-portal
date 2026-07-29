from django.db.models import QuerySet

from ..models import Game, GameResult, Player

def select_game_results(
    *, 
    player: Player, 
    game_type: Game.HumanPlayerMode,
) -> QuerySet[GameResult]:
    query_set = (
        GameResult.objects.filter(
            player=player,
            game__human_player_mode=game_type,
        )
        .select_related(
            "game",
            "player",
        )
    )

    return query_set