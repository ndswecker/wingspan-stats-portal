from django.db.models import Count

from ...models import Player, PlayerAchievement


def get_player_achievement_summary(
    *,
    player: Player,
):
    """
    Return the player's earned achievements,
    grouped by achievement type.

    Include the number of times each achievement
    has been earned.
    """

    return (
        PlayerAchievement.objects
        .filter(player=player)
        .values(
            "achievement__code",
            "achievement__name",
            "achievement__description",
        )
        .annotate(
            earned_count=Count("id"),
        )
        .order_by(
            "achievement__name",
        )
    )