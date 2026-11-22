
from calendar import month_name

from ...models import Player, PlayerAchievement


def get_player_achievement_summary(
    *,
    player: Player,
):
    """
    Return the player's achievements grouped by type.

    Include the number of times each achievement
    has been earned and the calendar months for
    recurring monthly achievements.
    """

    player_awards = (
        PlayerAchievement.objects
        .filter(player=player)
        .select_related("achievement")
        .order_by(
            "achievement__name",
            "period_start",
            "id",
        )
    )

    achievement_groups = {}

    for award in player_awards:
        achievement = award.achievement
        achievement_code = achievement.code

        if achievement_code not in achievement_groups:
            achievement_groups[achievement_code] = {
                "achievement__code": achievement.code,
                "achievement__name": achievement.name,
                "achievement__description": achievement.description,
                "earned_count": 0,
                "earned_periods": [],
                "earned_periods_label": "",
            }

        achievement_group = achievement_groups[achievement_code]

        achievement_group["earned_count"] += 1

        if award.period_start is not None:
            period_label = (
                f"{month_name[award.period_start.month]} "
                f"{award.period_start.year}"
            )

            achievement_group["earned_periods"].append(
                period_label
            )

    achievement_summary = list(achievement_groups.values())

    for achievement in achievement_summary:
        achievement["earned_periods_label"] = ", ".join(
            achievement["earned_periods"]
        )

    return achievement_summary
