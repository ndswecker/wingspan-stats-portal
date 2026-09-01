from django.db import transaction

from ..models import Game, GameResult, Player

@transaction.atomic
def create_game(
    *,
    game_data, 
    result_forms,
    acting_player: Player,
):
    game = Game.objects.create(
        date_played=game_data["date_played"],
        human_player_mode=game_data["human_player_mode"],
    )

    for form in result_forms:
        result_data = form.cleaned_data

        if not result_data.get("is_populated"):
            continue

        result_player = result_data["player"]
        is_confirmed = False
        if result_player == acting_player:
            is_confirmed = True

        GameResult.objects.create(
            game=game,
            player=result_data["player"],
            score=result_data["score"],
            turn_order=result_data["turn_order"],
            is_confirmed=is_confirmed
        )

    return game