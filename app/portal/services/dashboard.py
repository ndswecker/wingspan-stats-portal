"""
Services for the Wingspan Portal Home dashboard.

Responsibilities:
    - Build Community and Friends leaderboards.
    - Calculate player statistics from fully confirmed games.
    - Apply leaderboard time periods.
    - Rank players by average score or games played.

Player eligibility is determined by player_access.py.
Game-result eligibility is based on game confirmation status.
"""

from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.db.models import Avg, Count, Exists, OuterRef, QuerySet
from django.utils import timezone
from django.db.models import Avg, Count

from dataclasses import dataclass

from ..models import Game, GameResult, Player

from .player_access import (
    get_public_players,
    get_friends_leaderboard_players,
)

from .game_result_selection import (
    filter_fully_confirmed_game_results,
)


@dataclass
class LeaderboardRow:
    """
    Represent a single player's leaderboard statistics.

    The dashboard service creates these objects after
    aggregating eligible game results.

    Ranking and display formatting are applied later.
    """

    player: Player
    games_played: int
    average_score: Decimal
    rank: int | None = None


def get_total_games_played():
    """
    Return the total number of recorded games.

    This statistic includes all games, regardless of
    confirmation status or player visibility.
    """

    total_games = Game.objects.count()

    return total_games


def _select_leaderboard_results(
    *,
    players,
    start_date,
    end_date,
    game_type=None,
):
    """
    Return eligible GameResult records for a leaderboard.

    Results must:
        - Belong to one of the eligible Players.
        - Belong to a fully confirmed game.
        - Fall within the selected date period, if specified.
        - Match the selected game type, if specified.

    A game_type of None includes all game types.

    Returns a lazy QuerySet.
    """

    # Start with results belonging to eligible players.
    game_results = GameResult.objects.filter(
        player__in=players,
    )

    # Exclude games where any participant has not confirmed
    # their result.
    game_results = filter_fully_confirmed_game_results(
        game_results=game_results,
    )

    # Apply the lower date boundary when a period is selected.
    #
    # A None value represents the All Time option.
    if start_date is not None:
        game_results = game_results.filter(
            game__date_played__gte=start_date,
        )

    # Apply the upper date boundary.
    #
    # This prevents future-dated games from contributing
    # to leaderboard statistics.
    if end_date is not None:
        game_results = game_results.filter(
            game__date_played__lte=end_date,
        )

    # Optionally restrict results to a particular game type.
    #
    # A None value includes both Solo and Competitive games.
    if game_type is not None:
        game_results = game_results.filter(
            game__human_player_mode=game_type,
        )

    return game_results

def _aggregate_leaderboard_results(
    *,
    game_results,
):
    """
    Aggregate eligible GameResult records by Player.

    For each Player, calculate:
        - Number of games played
        - Average score

    Only Players with at least one eligible GameResult
    will appear in the returned statistics.

    Returns a dictionary keyed by Player ID.
    """

    # Group the results by the Player's primary key.
    #
    # Clear any default ordering before grouping.
    player_statistics = game_results.order_by().values(
        "player_id",
    )

    # Calculate the number of results and average score
    # for each Player.
    player_statistics = player_statistics.annotate(
        games_played=Count("id"),
        average_score=Avg("score"),
    )

    # Create a dictionary so we can efficiently
    # retrieve statistics for a particular Player.
    statistics_by_player = {}

    for statistics in player_statistics:

        player_id = statistics["player_id"]

        statistics_by_player[player_id] = {
            "games_played": statistics["games_played"],
            "average_score": statistics["average_score"],
        }

    return statistics_by_player


def _build_leaderboard_rows(
    *,
    players,
    statistics_by_player,
):
    """
    Build LeaderboardRow objects for eligible Players.

    Each row contains:
        - The Player object
        - Number of eligible games played
        - Average score

    Players without eligible game results are excluded.

    Rankings are assigned separately.
    """

    leaderboard_rows = []

    # Iterate through the eligible players.
    for player in players:

        # Find this player's aggregated statistics.
        player_statistics = statistics_by_player.get(
            player.pk,
        )

        # Players without qualifying games do not appear
        # in the ranked leaderboard.
        if player_statistics is None:
            continue

        # Retrieve the calculated statistics.
        games_played = player_statistics["games_played"]
        average_score = player_statistics["average_score"]

        # Normalize the average score to Decimal.
        #
        # Using str() avoids introducing additional floating-point
        # representation artifacts during conversion.
        average_score = Decimal(
            str(average_score),
        )

        # Package the Player and statistics into a row.
        leaderboard_row = LeaderboardRow(
            player=player,
            games_played=games_played,
            average_score=average_score,
        )

        leaderboard_rows.append(
            leaderboard_row,
        )

    return leaderboard_rows


def _rank_leaderboard_rows(
    *,
    leaderboard_rows,
    ranking_metric,
):
    """
    Sort and rank leaderboard rows by the selected metric.

    Supported ranking metrics:
        - average_score
        - games_played

    Players with identical metric values share the same rank.

    Rankings use standard competition ranking:
        1, 2, 2, 4

    Returns the sorted list of LeaderboardRow objects.
    """

    # Sort the leaderboard according to the selected metric.
    #
    # Player ID provides deterministic ordering when metric
    # values are identical.
    if ranking_metric == "average_score":

        ranked_rows = sorted(
            leaderboard_rows,
            key=lambda row: (
                -row.average_score,
                row.player.pk,
            ),
        )

    elif ranking_metric == "games_played":

        ranked_rows = sorted(
            leaderboard_rows,
            key=lambda row: (
                -row.games_played,
                row.player.pk,
            ),
        )

    else:
        raise ValueError(
            f"Unsupported leaderboard ranking metric: {ranking_metric}"
        )

    # Track the previous player's ranking value.
    previous_value = None
    previous_rank = None

    # Assign ranks in sorted order.
    for position, row in enumerate(
        ranked_rows,
        start=1,
    ):

        if ranking_metric == "average_score":
            current_value = row.average_score
        else:
            current_value = row.games_played

        # Players with identical values share a rank.
        if current_value == previous_value:
            row.rank = previous_rank

        # Otherwise, assign the current position as the rank.
        else:
            row.rank = position

        # Save the current values for the next iteration.
        previous_value = current_value
        previous_rank = row.rank

    return ranked_rows


def _build_leaderboard(
    *,
    players,
    start_date,
    end_date,
    ranking_metric,
    game_type=None,
    limit=None,
):
    """
    Build a ranked leaderboard for the supplied Players.

    A game_type of None includes all game types.
    A start_date of None includes all historical games.
    An end_date of None applies no upper date boundary.
    A limit of None returns every ranked player.

    Returns a list of LeaderboardRow objects.
    """

    # Step 1: Retrieve eligible game results.
    game_results = _select_leaderboard_results(
        players=players,
        start_date=start_date,
        end_date=end_date,
        game_type=game_type,
    )

    # Step 2: Aggregate statistics for each Player.
    statistics_by_player = _aggregate_leaderboard_results(
        game_results=game_results,
    )

    # Step 3: Construct LeaderboardRow objects.
    leaderboard_rows = _build_leaderboard_rows(
        players=players,
        statistics_by_player=statistics_by_player,
    )

    # Step 4: Sort players and assign their rankings.
    ranked_rows = _rank_leaderboard_rows(
        leaderboard_rows=leaderboard_rows,
        ranking_metric=ranking_metric,
    )

    # Step 5: Limit the number of displayed players, if requested.
    if limit is not None:
        ranked_rows = ranked_rows[:limit]

    return ranked_rows


def get_community_leaderboard(
    *,
    start_date,
    end_date,
    ranking_metric,
    game_type=None,
):
    """
    Return the Top 10 Community leaderboard.

    Only active Public players are eligible.

    Rankings include fully confirmed games within
    the selected time period.

    A game_type of None includes all game types.

    Returns a list of LeaderboardRow objects.
    """

    # Retrieve players who have opted into Public visibility.
    public_players = get_public_players()

    # Build and rank the leaderboard, limiting it to 10 players.
    community_leaderboard = _build_leaderboard(
        players=public_players,
        start_date=start_date,
        end_date=end_date,
        ranking_metric=ranking_metric,
        game_type=game_type,
        limit=10,
    )

    return community_leaderboard


def get_friends_leaderboard(
    *,
    user,
    start_date,
    end_date,
    ranking_metric,
    game_type=None,
):
    """
    Return the Friends leaderboard for an authenticated user.

    Eligible players include:
        - The authenticated user's own Player.
        - Their active friends, regardless of public status.

    Staff and superusers receive no special access.

    Rankings include fully confirmed games within
    the selected time period.

    A game_type of None includes all game types.

    Returns a list of LeaderboardRow objects.
    """

    # Retrieve the authenticated player and their active friends.
    friends_players = get_friends_leaderboard_players(
        user=user,
    )

    # Build and rank the complete Friends leaderboard.
    #
    # No row limit is applied.
    friends_leaderboard = _build_leaderboard(
        players=friends_players,
        start_date=start_date,
        end_date=end_date,
        ranking_metric=ranking_metric,
        game_type=game_type,
    )

    return friends_leaderboard