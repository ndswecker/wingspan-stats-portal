from datetime import date

from ...models import Game, GameResult, Player
from .monthly import MonthlyAchievement


class MonthlyGameCountAchievement(MonthlyAchievement):
    """
    Base implementation for monthly achievements
    earned by playing a specified number of games.
    """

    required_games: int
    game_mode: str

    @classmethod
    def evaluate(
        cls,
        *,
        player: Player,
        period_start: date,
        period_end: date,
    ) -> bool:

        game_count = GameResult.objects.filter(
            player=player,
            game__human_player_mode=cls.game_mode,
            game__date_played__gte=period_start,
            game__date_played__lt=period_end,
        ).count()

        return game_count >= cls.required_games


class BackyardBirderSolo(MonthlyGameCountAchievement):
    code = "backyard_birder_solo"
    name = "Backyard Birder - Solo"
    description = "Play at least 10 solo games in a calendar month."

    required_games = 10
    game_mode = Game.HumanPlayerMode.SINGLE


class BackyardBirderCompetitive(MonthlyGameCountAchievement):
    code = "backyard_birder_competitive"
    name = "Backyard Birder - Competitive"
    description = "Play at least 10 competitive games in a calendar month."

    required_games = 10
    game_mode = Game.HumanPlayerMode.MULTIPLE


class HardcoreListerSolo(MonthlyGameCountAchievement):
    code = "hardcore_lister_solo"
    name = "Hardcore Lister - Solo"
    description = "Play at least 30 solo games in a calendar month."

    required_games = 30
    game_mode = Game.HumanPlayerMode.SINGLE


class HardcoreListerCompetitive(MonthlyGameCountAchievement):
    code = "hardcore_lister_competitive"
    name = "Hardcore Lister - Competitive"
    description = "Play at least 30 competitive games in a calendar month."

    required_games = 30
    game_mode = Game.HumanPlayerMode.MULTIPLE