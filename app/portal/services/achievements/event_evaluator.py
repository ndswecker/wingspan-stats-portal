from ...models import (
    Achievement,
    Game,
    GameResult,
    PlayerAchievement,
)

from .registry import EVENT_ACHIEVEMENTS


def evaluate_game_achievements(
    *,
    game: Game,
) -> dict[str, list[GameResult]]:
    """
    Evaluate all registered event-based achievements
    against a single game.

    Create missing awards for qualifying results.
    Return qualifying results grouped by achievement code.
    """

    # Reload the game and its current results from the database.
    # The supplied game may contain stale prefetched results.
    game = Game.objects.prefetch_related(
        "results__player",
    ).get(
        pk=game.pk,
    )

    qualifying_achievements = {}

    for achievement_class in EVENT_ACHIEVEMENTS:
        qualifying_results = achievement_class.evaluate(
            game=game,
        )

        qualifying_achievements[achievement_class.code] = (
            qualifying_results
        )

        achievement = Achievement.objects.get(
            code=achievement_class.code,
        )

        for result in qualifying_results:
            PlayerAchievement.objects.get_or_create(
                achievement=achievement,
                source_result=result,
                defaults={
                    "player": result.player,
                },
            )

        qualifying_result_ids = [
            result.id for result in qualifying_results
        ]

        PlayerAchievement.objects.filter(
            achievement=achievement,
            source_result__game=game,
        ).exclude(
            source_result_id__in=qualifying_result_ids,
        ).delete()

    return qualifying_achievements