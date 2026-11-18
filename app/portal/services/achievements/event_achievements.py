from ...models import Game, GameResult
from .event import EventAchievement


class The180Club(EventAchievement):
    code = "the_180_club"
    name = "The 180 Club"
    description = "Score at least 180 points in a single game."

    @classmethod
    def evaluate(cls, *, game: Game) -> list[GameResult]:
        qualifying_results = []

        for result in game.results.all():
            if result.score >= 180:
                qualifying_results.append(result)

        return qualifying_results