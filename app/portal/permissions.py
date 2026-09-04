from django.contrib.auth.models import User

from .models import Game

def can_manage_game(
    user: User,
    game: Game,
) -> bool:
    if user.is_staff:
        return True

    requesting_player = getattr(user, "player", None)

    if requesting_player is None:
        return False

    # Get any results for this game that belong to the requesting player.
    matching_game_results = game.results.filter(
        player=requesting_player,
    )

    # If a result exists for the requesting player, then that player participated in this game.
    requesting_player_participates_in_game = matching_game_results.exists()

    if requesting_player_participates_in_game:
        return True
    else:
        return False
    