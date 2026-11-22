from datetime import date

from django.db import transaction

from ...models import Achievement, Player, PlayerAchievement

from .registry import MONTHLY_ACHIEVEMENTS


@transaction.atomic
def evaluate_monthly_achievements(
    *,
    player: Player,
    period_start: date,
    period_end: date,
) -> None:
    """
    Evaluate and reconcile all registered monthly achievements
    for a specific player and calendar month.

    The period starts on period_start (inclusive)
    and ends on period_end (exclusive).
    """

    for achievement_class in MONTHLY_ACHIEVEMENTS:

        qualifies = achievement_class.evaluate(
            player=player,
            period_start=period_start,
            period_end=period_end,
        )

        achievement = Achievement.objects.get(
            code=achievement_class.code,
        )

        if qualifies:
            # Create the award only if the player has not
            # already earned it for this period.
            PlayerAchievement.objects.get_or_create(
                player=player,
                achievement=achievement,
                period_start=period_start,
                defaults={
                    "period_end": period_end,
                },
            )

        else:
            # Remove the award if the player no longer
            # qualifies for this period.
            PlayerAchievement.objects.filter(
                player=player,
                achievement=achievement,
                period_start=period_start,
                source_result__isnull=True,
            ).delete()