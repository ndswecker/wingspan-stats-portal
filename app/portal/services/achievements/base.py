from abc import ABC

from ...models import (
    Achievement,
)

class BaseAchievement(ABC):
    """
    Base class for all achievements definitions.
    
    Provides shared metadata and database registration
    """

    code: str
    name: str
    description: str

    @classmethod
    def register(cls) -> Achievement:
        """
        Create or update this achievement's catalog record.

        Registration does not award the achievment to any player.
        """
        achievement, created = Achievement.objects.get_or_create(
            code=cls.code,
            defaults={
                "name": cls.name,
                "description": cls.description,
            },
        )
        return achievement