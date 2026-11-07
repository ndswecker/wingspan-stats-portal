from datetime import date

from django.db.models import Q, Count, Exists, OuterRef, QuerySet

from ..models import Game, GameResult, Player


def select_game_results(
    *,
    player: Player,
    game_type: Game.HumanPlayerMode,
    start_date: date | None = None,
    end_date: date | None = None,
    fully_confirmed_only: bool = False,
) -> QuerySet[GameResult]:
    """
    Select game results for a player, game type, and optional date range.

    When fully_confirmed_only=True, return only results belonging
    to games where every associated GameResult is confirmed.

    By default, include results regardless of confirmation status.
    """
    query_set = (
        GameResult.objects.filter(
            player=player,
            game__human_player_mode=game_type,
        )
        .select_related(
            "game",
            "player",
        )
    )

    if fully_confirmed_only:
        query_set = filter_fully_confirmed_game_results(
            game_results=query_set,
        )

        if start_date:
            query_set = query_set.filter(
                game__date_played__gte=start_date,
            )

        if end_date:
            query_set = query_set.filter(
                game__date_played__lte=end_date,
            )

        return query_set


def select_shared_games(
    *,
    primary_player: Player,
    secondary_player: Player,
    start_date: date | None = None,
    end_date: date | None = None,
    fully_confirmed_only: bool = False,
) -> QuerySet[Game]:
    """
    Select games shared by two specified players.

    A qualifying game must contain a GameResult for both players.
    Additional human participants are permitted.

    Optional date boundaries are inclusive.

    When fully_confirmed_only=True, exclude any game containing
    an unconfirmed GameResult, including results belonging to
    additional participants.

    By default, include games regardless of confirmation status.

    Returns a lazy QuerySet[Game] so callers can apply additional
    filtering, ordering, or prefetching before evaluation.
    """
    # Count results belonging to either selected player.
    #
    # The GameResult model enforces uniqueness of (game, player),
    # so a count of two guarantees that both players participated.
    #
    # Other participants do not affect this count.
    games = (
        Game.objects
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

    if fully_confirmed_only:
        # Build a correlated subquery to identify unconfirmed results
        # belonging to each candidate game.
        #
        # OuterRef("pk") references the Game currently being evaluated
        # by the outer queryset.
        unconfirmed_results = GameResult.objects.filter(
            game_id=OuterRef("pk"),
            is_confirmed=False,
        )

        # Exists() checks whether at least one unconfirmed result exists.
        #
        # Filtering the expression to False removes games containing
        # any unconfirmed results, regardless of which player owns them.
        #
        # alias() makes the expression available for filtering without
        # including the calculated Boolean in the returned Game objects.
        games = (
            games
            .alias(
                has_unconfirmed_results=Exists(unconfirmed_results),
            )
            .filter(
                has_unconfirmed_results=False,
            )
        )

    # Apply optional inclusive date boundaries.
    if start_date is not None:
        games = games.filter(
            date_played__gte=start_date,
        )

    if end_date is not None:
        games = games.filter(
            date_played__lte=end_date,
        )

    return games


def filter_fully_confirmed_game_results(
    *,
    game_results: QuerySet[GameResult],
) -> QuerySet[GameResult]:
    """
    Return only results belonging to fully confirmed games.

    A game is fully confirmed when none of its
    associated GameResult records are unconfirmed.

    Accepts and returns a lazy QuerySet.
    """

    # Find unconfirmed results belonging to the game
    # associated with each candidate GameResult.
    unconfirmed_results = GameResult.objects.filter(
        game_id=OuterRef("game_id"),
        is_confirmed=False,
    )

    # Exclude results belonging to games with
    # at least one unconfirmed participant.
    confirmed_results = game_results.alias(
        has_unconfirmed_results=Exists(unconfirmed_results),
    )

    confirmed_results = confirmed_results.filter(
        has_unconfirmed_results=False,
    )

    return confirmed_results