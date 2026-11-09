
import random

from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from ...models import Game, GameResult, Player

from .seed_players import SEED_GROUP_NAME, SEED_PLAYERS


# Fixed seed makes the random game generation reproducible.
RANDOM_SEED = 2026


# Typical scoring ability for each synthetic player.
# Actual results vary around these values.
PLAYER_SCORE_AVERAGES = {
    "seed_kestrel": 105,
    "seed_barn_owl": 92,
    "seed_blue_jay": 85,
    "seed_waxwing": 98,
    "seed_junco": 74,
    "seed_heron": 110,
    "seed_finch": 88,
    "seed_killdeer": 79,
    "seed_chickadee": 95,
    "seed_flicker": 90,
    "seed_osprey": 102,
    "seed_hawk": 108,
    "seed_egret": 82,
    "seed_swallow": 91,
    "seed_tanager": 100,
}


def get_seed_players():
    """
    Retrieve and validate all 15 synthetic players.

    Every player must have a matching Django User that
    belongs to the synthetic development group.
    """
    try:
        seed_group = Group.objects.get(
            name=SEED_GROUP_NAME,
        )
    except Group.DoesNotExist:
        raise CommandError(
            "Seed group does not exist. Run seed_players first."
        )

    players_by_handle = {}

    for name, handle, _ in SEED_PLAYERS:

        player = (
            Player.objects
            .select_related("user")
            .filter(handle=handle)
            .first()
        )

        if player is None:
            raise CommandError(
                f"Missing seed player: {handle}"
            )

        if (
            player.name != name
            or player.user is None
            or player.user.username != handle
        ):
            raise CommandError(
                f"Invalid seed player relationship: {handle}"
            )

        if not player.user.groups.filter(
            pk=seed_group.pk,
        ).exists():
            raise CommandError(
                f"Player is not marked as seed data: {handle}"
            )

        players_by_handle[handle] = player

    return players_by_handle


def build_game_schedule():
    """
    Build a year of synthetic game activity.

    A schedule entry contains:
        (days_ago, participant_handles)

    Different groups intentionally have different activity
    patterns, including repeated sessions and long gaps.
    """
    schedule = []

    def add_game(days_ago, handles):
        schedule.append(
            (days_ago, tuple(handles))
        )

    # Generate activity across the past 365 days.
    for days_ago in range(365):

        # --------------------------------------------------
        # Group A: Frequent competitive players
        # --------------------------------------------------
        # Kestrel, Barn Owl, and Blue Jay regularly play
        # against each other, sometimes multiple times daily.
        if days_ago % 4 == 0:

            add_game(
                days_ago,
                [
                    "seed_kestrel",
                    "seed_barn_owl",
                    "seed_blue_jay",
                ],
            )

            # Additional game during certain sessions.
            if days_ago % 20 == 0:

                add_game(
                    days_ago,
                    [
                        "seed_kestrel",
                        "seed_barn_owl",
                    ],
                )

        # --------------------------------------------------
        # Group B: Regular competitive opponents
        # --------------------------------------------------
        # These players have been active primarily during
        # the more recent portion of the year.
        if (
            days_ago <= 240
            and days_ago % 6 == 1
        ):

            add_game(
                days_ago,
                [
                    "seed_heron",
                    "seed_osprey",
                    "seed_hawk",
                ],
            )

        # --------------------------------------------------
        # Group C: Weekly gaming sessions
        # --------------------------------------------------
        if days_ago % 9 == 2:

            add_game(
                days_ago,
                [
                    "seed_finch",
                    "seed_chickadee",
                    "seed_swallow",
                ],
            )

        # --------------------------------------------------
        # Group D: Players with long inactivity gaps
        # --------------------------------------------------
        # No competitive sessions within the last 65 days.
        # Another gap exists farther back in their history.
        if (
            days_ago >= 65
            and not 125 <= days_ago <= 190
            and days_ago % 9 == 3
        ):

            add_game(
                days_ago,
                [
                    "seed_waxwing",
                    "seed_junco",
                    "seed_killdeer",
                ],
            )

        # --------------------------------------------------
        # Group E: Occasional competitive sessions
        # --------------------------------------------------
        if days_ago % 11 == 5:

            add_game(
                days_ago,
                [
                    "seed_barn_owl",
                    "seed_flicker",
                    "seed_egret",
                ],
            )

    # ------------------------------------------------------
    # Solo games
    # ------------------------------------------------------
    # Each player has a different interval and offset.
    # This distributes solo games across the entire year.
    for player_index, (_, handle, _) in enumerate(
        SEED_PLAYERS
    ):

        interval = 39 + (player_index % 8)
        offset = player_index % interval

        # Western Tanager plays solo more frequently.
        if handle == "seed_tanager":
            interval = 25
            offset = 0

        for days_ago in range(365):

            if days_ago % interval != offset:
                continue

            # Preserve the inactivity gap for this group.
            if handle in {
                "seed_waxwing",
                "seed_junco",
                "seed_killdeer",
            }:
                if days_ago < 65:
                    continue

                if 125 <= days_ago <= 190:
                    continue

            add_game(
                days_ago,
                [handle],
            )

    # Oldest games first.
    # Python's stable sort preserves the order of multiple
    # games scheduled on the same day.
    schedule.sort(
        key=lambda entry: entry[0],
        reverse=True,
    )

    return schedule


def generate_score(*, handle, rng):
    """
    Generate a realistic score with player-specific ability.

    Scores are normally distributed around the player's
    typical average, with moderate variation.
    """
    average = PLAYER_SCORE_AVERAGES[handle]

    score = round(
        rng.gauss(
            mu=average,
            sigma=15,
        )
    )

    # Keep scores within a plausible testing range.
    return max(30, min(180, score))


def generate_confirmation_states(*, player_count, rng):
    """
    Generate confirmation states for all participants.

    Solo games are automatically fully confirmed.

    Competitive games are approximately:
      80% fully confirmed
      15% partially confirmed
       5% entirely unconfirmed
    """
    if player_count == 1:
        return [True]

    confirmation_roll = rng.random()

    if confirmation_roll < 0.80:
        return [True] * player_count

    if confirmation_roll < 0.95:

        # Ensure at least one participant is confirmed
        # and at least one remains unconfirmed.
        confirmed_count = rng.randint(
            1,
            player_count - 1,
        )

        states = (
            [True] * confirmed_count
            + [False] * (player_count - confirmed_count)
        )

        rng.shuffle(states)
        return states

    return [False] * player_count


def create_synthetic_game(
    *,
    date_played,
    participant_handles,
    players_by_handle,
    rng,
):
    """
    Create one Game and its associated GameResults.

    Every participant receives a unique turn order.
    """
    player_count = len(participant_handles)

    if player_count == 1:
        game_type = Game.HumanPlayerMode.SINGLE

    else:
        game_type = Game.HumanPlayerMode.MULTIPLE

    game = Game.objects.create(
        date_played=date_played,
        human_player_mode=game_type,
    )

    # Randomize the participants' turn order.
    turn_order_handles = list(participant_handles)
    rng.shuffle(turn_order_handles)

    confirmation_states = generate_confirmation_states(
        player_count=player_count,
        rng=rng,
    )

    for turn_order, handle in enumerate(
        turn_order_handles,
        start=1,
    ):

        GameResult.objects.create(
            game=game,
            player=players_by_handle[handle],
            turn_order=turn_order,
            score=generate_score(
                handle=handle,
                rng=rng,
            ),
            is_confirmed=confirmation_states[
                turn_order - 1
            ],
        )

    return game


class Command(BaseCommand):
    help = "Generate synthetic games and results for local development."

    def handle(self, *args, **options):

        # Require the development Django settings module.
        if (
            not settings.DEBUG
            or settings.SETTINGS_MODULE != "config.settings.development"
        ):
            raise CommandError(
                "This command can only run with the "
                "development settings module and DEBUG=True."
            )

        # Use a dedicated random generator so this command
        # does not depend on global random state.
        rng = random.Random(RANDOM_SEED)

        created_games = 0
        created_results = 0

        solo_games = 0
        competitive_games = 0

        fully_confirmed_games = 0
        partially_confirmed_games = 0
        unconfirmed_games = 0

        with transaction.atomic():

            players_by_handle = get_seed_players()

            # Game has no synthetic-data marker yet.
            #
            # Refuse to generate another dataset when any
            # synthetic player already has game history.
            # This prevents duplicate game generation.
            existing_seed_results = GameResult.objects.filter(
                player__in=players_by_handle.values(),
            )

            if existing_seed_results.exists():
                self.stdout.write(
                    self.style.WARNING(
                        "Synthetic players already have game "
                        "results. No new games were generated."
                    )
                )
                return

            schedule = build_game_schedule()
            today = timezone.localdate()

            for days_ago, participant_handles in schedule:

                date_played = (
                    today - timedelta(days=days_ago)
                )

                game = create_synthetic_game(
                    date_played=date_played,
                    participant_handles=participant_handles,
                    players_by_handle=players_by_handle,
                    rng=rng,
                )

                created_games += 1

                game_results = list(
                    GameResult.objects.filter(game=game)
                )

                created_results += len(game_results)

                if game.human_player_mode == Game.HumanPlayerMode.SINGLE:
                    solo_games += 1
                else:
                    competitive_games += 1

                confirmation_states = [
                    result.is_confirmed
                    for result in game_results
                ]

                if all(confirmation_states):
                    fully_confirmed_games += 1

                elif any(confirmation_states):
                    partially_confirmed_games += 1

                else:
                    unconfirmed_games += 1

        self.stdout.write(
            self.style.SUCCESS(
                "Synthetic game seeding completed successfully."
            )
        )

        self.stdout.write(
            f"Games created: {created_games}"
        )

        self.stdout.write(
            f"Game results created: {created_results}"
        )

        self.stdout.write(
            f"Solo games: {solo_games}"
        )

        self.stdout.write(
            f"Competitive games: {competitive_games}"
        )

        self.stdout.write(
            f"Fully confirmed games: {fully_confirmed_games}"
        )

        self.stdout.write(
            f"Partially confirmed games: {partially_confirmed_games}"
        )

        self.stdout.write(
            f"Unconfirmed games: {unconfirmed_games}"
        )
