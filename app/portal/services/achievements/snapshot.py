from dataclasses import dataclass
from datetime import date

from ...models import Game, GameResult


@dataclass(frozen=True)
class GameAchievementSnapshot:
    """
    Represents the state of a game relevant
    to achievement reevaluation.
    """

    date_played: date
    human_player_mode: str
    player_ids: frozenset[int]

    @classmethod
    def from_game(cls, *, game: Game) -> "GameAchievementSnapshot":
        """
        Capture the current persisted game state.

        Query the database rather than relying on
        potentially stale or modified model instances.
        """

        current_game = Game.objects.get(pk=game.pk)

        player_ids = frozenset(
            GameResult.objects.filter(
                game_id=current_game.pk,
            ).values_list(
                "player_id",
                flat=True,
            )
        )

        return cls(
            date_played=current_game.date_played,
            human_player_mode=current_game.human_player_mode,
            player_ids=player_ids,
        )