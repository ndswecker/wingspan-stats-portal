from dataclasses import dataclass
from decimal import Decimal

from .models import Player


@dataclass(frozen=True)
class PlayerPerformanceSummary:
    player: Player
    games_played: int
    game_wins: int
    night_wins: int
    average_score: Decimal | None