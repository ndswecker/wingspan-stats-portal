from abc import abstractmethod
from datetime import date

from ...models import Player
from .base import BaseAchievement


class MonthlyAchievement(BaseAchievement):
    """
    Base class for achievements earned once per
    player per calendar month.
    """

    @classmethod
    @abstractmethod
    def evaluate(
        cls,
        *,
        player: Player,
        period_start: date,
        period_end: date,
    ) -> bool:
        """
        Determine whether a player qualifies for
        this achievement during the given period.

        period_start is inclusive.
        period_end is exclusive.

        Eligibility evaluation must not modify
        database records.
        """
        raise NotImplementedError