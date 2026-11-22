from datetime import date

from ...models import Game, Player

from .snapshot import GameAchievementSnapshot
from .event_evaluator import evaluate_game_achievements
from .monthly_evaluator import evaluate_monthly_achievements


def get_month_boundaries(
    *,
    date_played: date,
) -> tuple[date, date]:
    """
    Return the inclusive start and exclusive end
    of the calendar month containing date_played.
    """

    period_start = date(
        date_played.year,
        date_played.month,
        1,
    )

    if date_played.month == 12:
        period_end = date(
            date_played.year + 1,
            1,
            1,
        )
    else:
        period_end = date(
            date_played.year,
            date_played.month + 1,
            1,
        )

    return period_start, period_end


def synchronize_game_achievements(
    *,
    game: Game | None,
    previous_state: GameAchievementSnapshot | None,
) -> None:
    """
    Coordinate achievement evaluation following
    game creation, modification, or deletion.

    Reconcile event awards for the current game,
    then reconcile monthly awards for all affected
    players and calendar months.
    """

    affected_player_months = set()

    # Capture the original players and month.
    if previous_state is not None:
        previous_period_start, previous_period_end = (
            get_month_boundaries(
                date_played=previous_state.date_played,
            )
        )

        for player_id in previous_state.player_ids:
            affected_player_months.add(
                (
                    player_id,
                    previous_period_start,
                    previous_period_end,
                )
            )

    # Evaluate the current game and capture its
    # current players and month.
    if game is not None:
        evaluate_game_achievements(
            game=game,
        )

        current_state = GameAchievementSnapshot.from_game(
            game=game,
        )

        current_period_start, current_period_end = (
            get_month_boundaries(
                date_played=current_state.date_played,
            )
        )

        for player_id in current_state.player_ids:
            affected_player_months.add(
                (
                    player_id,
                    current_period_start,
                    current_period_end,
                )
            )

    # Reconcile monthly achievements for each
    # affected player and month.
    for (
        player_id,
        period_start,
        period_end,
    ) in sorted(affected_player_months):

        player = Player.objects.get(
            pk=player_id,
        )

        evaluate_monthly_achievements(
            player=player,
            period_start=period_start,
            period_end=period_end,
        )