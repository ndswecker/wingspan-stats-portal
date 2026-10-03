from dataclasses import dataclass
from datetime import date

from django.db.models import Count, Prefetch, Q

from ..models import Game, GameResult, Player


@dataclass(frozen=True)
class GameScoreGap:
    """One shared game's score-gap data for the selected players."""

    game_id: int
    date_played: date
    primary_score: int
    secondary_score: int
    low_score: int
    high_score: int
    score_gap: int
    winner: Player | None


def select_game_score_gaps(
    *,
    primary_player: Player,
    secondary_player: Player,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[GameScoreGap]:
    """
    Select shared games and calculate score-gap data for two players.

    A game qualifies when both selected players have a result in the game.
    Other players may also have participated. Optional date boundaries are
    inclusive.
    """
    games = (
        Game.objects
        # Count only results belonging to the two selected players. We do not
        # restrict the total result count because multiplayer games with
        # additional participants are valid for Game Score Gap.
        .annotate(
            selected_player_count=Count(
                "results",
                filter=Q(
                    results__player__in=[
                        primary_player,
                        secondary_player,
                    ]
                ),
            ),
        )
        .filter(
            selected_player_count=2,
        )
    )

    if start_date is not None:
        games = games.filter(
            date_played__gte=start_date,
        )

    if end_date is not None:
        games = games.filter(
            date_played__lte=end_date,
        )

    # Fetch only the two results needed by this feature. The GameResult model
    # guarantees one result per player per game, so each qualifying game will
    # provide exactly one primary and one secondary result here.
    selected_results = (
        GameResult.objects
        .filter(
            player__in=[
                primary_player,
                secondary_player,
            ],
        )
        .select_related("player")
    )

    games = (
        games
        .prefetch_related(
            Prefetch(
                "results",
                queryset=selected_results,
                to_attr="game_score_gap_results",
            )
        )
        # Score Gap is a game-by-game progression, so display the oldest game
        # first. Game ID provides deterministic ordering for same-day games.
        .order_by(
            "date_played",
            "id",
        )
    )

    score_gaps = []

    for game in games:
        results_by_player = {
            result.player_id: result
            for result in game.game_score_gap_results
        }

        primary_result = results_by_player[primary_player.id]
        secondary_result = results_by_player[secondary_player.id]

        primary_score = primary_result.score
        secondary_score = secondary_result.score

        low_score = min(
            primary_score,
            secondary_score,
        )
        high_score = max(
            primary_score,
            secondary_score,
        )

        if primary_score > secondary_score:
            winner = primary_player
        elif secondary_score > primary_score:
            winner = secondary_player
        else:
            winner = None

        score_gaps.append(
            GameScoreGap(
                game_id=game.id,
                date_played=game.date_played,
                primary_score=primary_score,
                secondary_score=secondary_score,
                low_score=low_score,
                high_score=high_score,
                score_gap=high_score - low_score,
                winner=winner,
            )
        )

    return score_gaps
