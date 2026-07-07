from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from .models import GameResult, Player, Game


@dataclass(frozen=True)
class PlayerPerformanceSummary:
    player: Player
    games_played: int
    game_wins: int
    night_wins: int
    average_score: Decimal | None

@dataclass(frozen=True)
class GameSummary:
    game: Game
    results: list[GameResult]
    game_winner: Player | None

@dataclass(frozen=True)
class NightSummary:
    date_played: date
    games: list[GameSummary]
    night_winner: Player | None