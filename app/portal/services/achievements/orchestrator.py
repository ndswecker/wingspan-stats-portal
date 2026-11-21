from ...models import Game

from .snapshot import GameAchievementSnapshot
from .event_evaluator import evaluate_game_achievements


def synchronize_game_achievements(
    *,
    game: Game | None,
    previous_state: GameAchievementSnapshot | None,
) -> None:
    """
    Coordinate achievement evaluation following
    a game creation, update, or deletion.

    The previous state identifies affected historical
    achievement scopes.

    The current game identifies the latest persisted state.
    """

    # Evaluate achievements linked to individual game results.
    if game is not None:
        evaluate_game_achievements(
            game=game,
        )