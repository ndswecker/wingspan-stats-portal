from datetime import date

from django.db.models import QuerySet

from ..models import Game, GameResult, Player

def select_game_results(
    *, 
    player: Player, 
    game_type: Game.HumanPlayerMode,
    start_date: date | None = None,
    end_date: date | None = None,
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

    if start_date and end_date:
        query_set = query_set.filter(
            game__date_played__gte=start_date,
        )   

    if end_date:
        query_set = query_set.filter(
            game__date_played__lte=end_date,
        )
 
    return query_set