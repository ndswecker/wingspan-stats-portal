from dataclasses import dataclass
from datetime import date
from itertools import groupby

from django.db.models import Count, Q, Prefetch

from ..models import Player, Game, GameResult


@dataclass(frozen=True)
class FeatheredFoeGameResult:
    """One player's result within a qualifying feathered foe game."""
    player: Player
    score: int
    turn_order: int | None

@dataclass(frozen=True)
class FeatheredFoeGame:
    """ One qualifying two-player game. A winner of None represents a tie. """
    game_id: int
    date_played: date
    winner: Player | None
    results: list[FeatheredFoeGameResult]

@dataclass(frozen=True)
class FeatheredFoeNightPlayerSummary:
    """ One players aggregate results for a single night."""
    player: Player
    score_total: int
    game_wins: int
    game_losses: int

@dataclass(frozen=True)
class FeatheredFoeNight:
    """ All qualifying games played by the select players on one date.
    A winner of None represents a tie for the night.
    """
    date_played: date
    winner: Player | None
    player_summaries: list[FeatheredFoeNightPlayerSummary]
    games: list[FeatheredFoeGame]

@dataclass(frozen=True)
class FeatheredFoeNightSummary:
    """
    Calculate result of a single Feathered Foe Night.

    Player summaries are ordered with the primary player first
    """
    winner: Player | None
    player_summaries: list[FeatheredFoeNightPlayerSummary]

@dataclass(frozen=True)
class FeatheredFoePlayerSummary:
    """ One player's aggregate results across the complete selected date range."""
    player: Player
    score_total: int
    game_wins: int
    game_losses: int
    night_wins: int
    night_losses: int

@dataclass(frozen=True)
class FeatheredFoe:
    """
    Complete feathered foe result for two selected players.
    
    Current winner is determined by total game wins, and if tied,
    by total score across all games.
    """
    primary_player: Player
    secondary_player: Player
    current_winner: Player | None
    player_summaries: list[FeatheredFoePlayerSummary]
    nights: list[FeatheredFoeNight]


def select_feathered_foe_games(
    *,
    primary_player: Player,
    secondary_player: Player,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[Game]:
    """
    Select competitive games played exclusively by the two players.
    
    A qualifying game must contain both selected players and exactly
    two player results. Optional boundaries are inclusive.

    Game results and their associated players are prefetched for 
    downstream processing.
    """
    games = (
        Game.objects
        .filter(
            human_player_mode=Game.HumanPlayerMode.MULTIPLE,
        )
        .annotate(
            total_result_count=Count(
                "results",
            ),
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
            total_result_count=2,
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

    games = games.prefetch_related(
        Prefetch(
            "results",
            queryset=GameResult.objects.select_related("player"),
            to_attr="feathered_foe_results",
        )
    )

    games = games.order_by(
        "-date_played",
        "-id",
    )

    games = list(games)

    return games


def build_feathered_foe_game(
    *,
    game: Game,
    primary_player: Player,
    secondary_player: Player,
) -> FeatheredFoeGame:
    """
    Build a Feathered Foe game from a qualifying game.
    
    The game is expected to contain exactly two prefetched player results.
    """
    game_results_by_player = {
        result.player_id: result
        for result in game.feathered_foe_results
    }

    primary_game_result = game_results_by_player[primary_player.id]
    secondary_game_result = game_results_by_player[secondary_player.id]

    primary_result = FeatheredFoeGameResult(
        player=primary_player,
        score=primary_game_result.score,
        turn_order=primary_game_result.turn_order,
    )

    secondary_result = FeatheredFoeGameResult(
        player=secondary_player,
        score=secondary_game_result.score,
        turn_order=secondary_game_result.turn_order,
    )

    feathered_foe_results = [
        primary_result,
        secondary_result,
    ]

    winner = None
    if primary_result.score > secondary_result.score:
        winner = primary_player
    elif secondary_result.score > primary_result.score:
        winner = secondary_player

    feathered_foe_game = FeatheredFoeGame(
        game_id=game.id,
        date_played=game.date_played,
        winner=winner,
        results=feathered_foe_results,
    )

    return feathered_foe_game

def determine_feathered_foe_night_winner(
    *,
    primary_summary: FeatheredFoeNightPlayerSummary,
    secondary_summary: FeatheredFoeNightPlayerSummary,
) -> Player | None:
    """
    Determine the winner of a Feathered Foe night.

    Game wins are compared first. If game wins are tied,
    total score is used as the tiebreaker. If both are tied,
    the night has no winner.
    """
    if primary_summary.game_wins > secondary_summary.game_wins:
        return primary_summary.player

    if secondary_summary.game_wins > primary_summary.game_wins:
        return secondary_summary.player

    if primary_summary.score_total > secondary_summary.score_total:
        return primary_summary.player

    if secondary_summary.score_total > primary_summary.score_total:
        return secondary_summary.player

    return None

def build_feathered_foe_night_summary(
    *,
    games: list[FeatheredFoeGame],
    primary_player: Player,
    secondary_player: Player,
) -> FeatheredFoeNightSummary:
    """
    Calculate player summaries and the winner for one Feathered Foe night.

    All games are expected to belong to the same date.
    """
    primary_score_total = 0
    primary_game_wins = 0
    primary_game_losses = 0

    secondary_score_total = 0
    secondary_game_wins = 0
    secondary_game_losses = 0

    for game in games:
        primary_result = game.results[0]
        secondary_result = game.results[1]

        primary_score_total += primary_result.score
        secondary_score_total += secondary_result.score

        if game.winner == primary_player:
            primary_game_wins += 1
            secondary_game_losses += 1
        elif game.winner == secondary_player:
            secondary_game_wins += 1
            primary_game_losses += 1

    primary_summary = FeatheredFoeNightPlayerSummary(
        player=primary_player,
        score_total=primary_score_total,
        game_wins=primary_game_wins,
        game_losses=primary_game_losses,
    )

    secondary_summary = FeatheredFoeNightPlayerSummary(
        player=secondary_player,
        score_total=secondary_score_total,
        game_wins=secondary_game_wins,
        game_losses=secondary_game_losses,
    )

    winner = determine_feathered_foe_night_winner(
        primary_summary=primary_summary,
        secondary_summary=secondary_summary,
    )

    night_summary = FeatheredFoeNightSummary(
        winner=winner,
        player_summaries=[
            primary_summary,
            secondary_summary,
        ],
    )

    return night_summary

def build_feathered_foe_nights(
    *,
    games: list[FeatheredFoeGame],
    primary_player: Player,
    secondary_player: Player,
) -> list[FeatheredFoeNight]:
    """
    Build Feathered Foe nights from qualifying games.

    Games are expected to be ordered by date played descending.
    """
    nights = []

    for date_played, grouped_games in groupby(
        games,
        key=lambda game: game.date_played,
    ):
        night_games = list(grouped_games)

        night_summary = build_feathered_foe_night_summary(
            games=night_games,
            primary_player=primary_player,
            secondary_player=secondary_player,
        )

        night = FeatheredFoeNight(
            date_played=date_played,
            winner=night_summary.winner,
            player_summaries=night_summary.player_summaries,
            games=night_games,
        )

        nights.append(night)

    return nights

def build_feathered_foe_player_summaries(
    *,
    nights: list[FeatheredFoeNight],
    primary_player: Player,
    secondary_player: Player,
) -> list[FeatheredFoePlayerSummary]:
    """
    Build aggregate player summaries across all Feathered Foe nights.

    Player summaries are returned with the primary player first
    and the secondary player second.
    """
    primary_score_total = 0
    primary_game_wins = 0
    primary_game_losses = 0
    primary_night_wins = 0
    primary_night_losses = 0

    secondary_score_total = 0
    secondary_game_wins = 0
    secondary_game_losses = 0
    secondary_night_wins = 0
    secondary_night_losses = 0

    for night in nights:
        primary_night_summary = night.player_summaries[0]
        secondary_night_summary = night.player_summaries[1]

        primary_score_total += primary_night_summary.score_total
        primary_game_wins += primary_night_summary.game_wins
        primary_game_losses += primary_night_summary.game_losses

        secondary_score_total += secondary_night_summary.score_total
        secondary_game_wins += secondary_night_summary.game_wins
        secondary_game_losses += secondary_night_summary.game_losses

        if night.winner == primary_player:
            primary_night_wins += 1
            secondary_night_losses += 1
        elif night.winner == secondary_player:
            secondary_night_wins += 1
            primary_night_losses += 1

    primary_summary = FeatheredFoePlayerSummary(
        player=primary_player,
        score_total=primary_score_total,
        game_wins=primary_game_wins,
        game_losses=primary_game_losses,
        night_wins=primary_night_wins,
        night_losses=primary_night_losses,
    )

    secondary_summary = FeatheredFoePlayerSummary(
        player=secondary_player,
        score_total=secondary_score_total,
        game_wins=secondary_game_wins,
        game_losses=secondary_game_losses,
        night_wins=secondary_night_wins,
        night_losses=secondary_night_losses,
    )

    player_summaries = [
        primary_summary,
        secondary_summary,
    ]

    return player_summaries

def determine_feathered_foe_current_winner(
    *,
    primary_summary: FeatheredFoePlayerSummary,
    secondary_summary: FeatheredFoePlayerSummary,
) -> Player | None:
    """
    Determine the current Feathered Foe winner.

    Game wins are compared first. If game wins are tied,
    total score is used as the tiebreaker. If both are tied,
    there is no current winner.
    """
    if primary_summary.game_wins > secondary_summary.game_wins:
        return primary_summary.player

    if secondary_summary.game_wins > primary_summary.game_wins:
        return secondary_summary.player

    if primary_summary.score_total > secondary_summary.score_total:
        return primary_summary.player

    if secondary_summary.score_total > primary_summary.score_total:
        return secondary_summary.player

    return None

def build_feathered_foe(
    *,
    primary_player: Player,
    secondary_player: Player,
    start_date: date | None = None,
    end_date: date | None = None,
) -> FeatheredFoe:
    """
    Build the complete Feathered Foe result for two players
    within the selected date range.
    """
    games = select_feathered_foe_games(
        primary_player=primary_player,
        secondary_player=secondary_player,
        start_date=start_date,
        end_date=end_date,
    )

    feathered_foe_games = [
        build_feathered_foe_game(
            game=game,
            primary_player=primary_player,
            secondary_player=secondary_player,
        )
        for game in games
    ]

    nights = build_feathered_foe_nights(
        games=feathered_foe_games,
        primary_player=primary_player,
        secondary_player=secondary_player,
    )

    player_summaries = build_feathered_foe_player_summaries(
        nights=nights,
        primary_player=primary_player,
        secondary_player=secondary_player,
    )

    primary_summary = player_summaries[0]
    secondary_summary = player_summaries[1]

    current_winner = determine_feathered_foe_current_winner(
        primary_summary=primary_summary,
        secondary_summary=secondary_summary,
    )

    feathered_foe = FeatheredFoe(
        primary_player=primary_player,
        secondary_player=secondary_player,
        current_winner=current_winner,
        player_summaries=player_summaries,
        nights=nights,
    )

    return feathered_foe
