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


class TheDodo(EventAchievement):
    code = "the_dodo"
    name = "The Dodo"
    description = "Score fewer than 80 points in a single game."

    @classmethod
    def evaluate(cls, *, game: Game) -> list[GameResult]:
        qualifying_results = []

        for result in game.results.all():
            if result.score < 80:
                qualifying_results.append(result)

        return qualifying_results


class TheShrike(EventAchievement):
    code = "the_shrike"
    name = "The Shrike"
    description = "Win a competitive game by at least 30 points and leave your competition impaled on a thorn. "

    @classmethod
    def evaluate(cls, *, game: Game) -> list[GameResult]:

        if game.human_player_mode != Game.HumanPlayerMode.MULTIPLE:
            return []

        results = sorted(
            game.results.all(),
            key=lambda result: result.score,
            reverse=True,
        )

        if len(results) < 2:
            return []

        winning_result = results[0]
        second_place_result = results[1]

        winning_margin = (
            winning_result.score - second_place_result.score
        )

        if winning_margin >= 30:
            return [winning_result]

        return []

class TheImpaledShrew(EventAchievement):
    code = "the_impaled_shrew"
    name = "The Impaled Shrew"
    description = "Lose by at least 30 points in a competitive game and find yourself impaled on a thorn by the merciless Shrike."

    @classmethod
    def evaluate(cls, *, game: Game) -> list[GameResult]:

        if game.human_player_mode != Game.HumanPlayerMode.MULTIPLE:
            return []

        results = list(game.results.all())

        if len(results) < 2:
            return []

        winning_score = max(
            result.score for result in results
        )

        qualifying_results = []

        for result in results:
            score_difference = winning_score - result.score

            if score_difference >= 30:
                qualifying_results.append(result)

        return qualifying_results