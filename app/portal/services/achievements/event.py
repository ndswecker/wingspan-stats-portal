from abc import abstractmethod

from ...models import Game, GameResult
from .base import BaseAchievement


class EventAchievement(BaseAchievement):
    """
    Base class for achievements evaluated against
    an individual game.
    """

    @classmethod
    @abstractmethod
    def evaluate(cls, *, game: Game) -> list[GameResult]:
        """
        Return the GameResult records that qualify
        for this achievement.

        This method must not modify the database.
        """
        raise NotImplementedError