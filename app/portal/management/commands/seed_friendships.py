
from django.conf import settings
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from ...models import Friendship, Player


# Must match the group created by seed_players.py.
SEED_GROUP_NAME = "wingspan_seed_data"


# Active friendship pairs.
# Each pair uses the bird's synthetic username/handle.
#
# Western Tanager is intentionally excluded so that
# we can test a player with no friends.
ACTIVE_FRIENDSHIPS = [
    # Kestrel's social circle
    ("seed_kestrel", "seed_barn_owl"),
    ("seed_kestrel", "seed_blue_jay"),
    ("seed_kestrel", "seed_waxwing"),
    ("seed_kestrel", "seed_heron"),
    ("seed_kestrel", "seed_finch"),
    ("seed_kestrel", "seed_chickadee"),
    ("seed_kestrel", "seed_hawk"),

    # Barn Owl's additional friends
    ("seed_barn_owl", "seed_blue_jay"),
    ("seed_barn_owl", "seed_junco"),
    ("seed_barn_owl", "seed_osprey"),
    ("seed_barn_owl", "seed_flicker"),
    ("seed_barn_owl", "seed_egret"),

    # Blue Jay's additional friends
    ("seed_blue_jay", "seed_killdeer"),
    ("seed_blue_jay", "seed_swallow"),
    ("seed_blue_jay", "seed_finch"),

    # Smaller friendship groups
    ("seed_waxwing", "seed_junco"),
    ("seed_waxwing", "seed_heron"),
    ("seed_heron", "seed_osprey"),
    ("seed_heron", "seed_hawk"),
    ("seed_finch", "seed_chickadee"),
    ("seed_finch", "seed_swallow"),
    ("seed_flicker", "seed_hawk"),
    ("seed_egret", "seed_swallow"),
    ("seed_killdeer", "seed_junco"),
]


# Historical friendships that have already ended.
#
# Each entry contains:
# (first player, second player, player who ended it)
ENDED_FRIENDSHIPS = [
    ("seed_kestrel", "seed_osprey", "seed_kestrel"),
    ("seed_barn_owl", "seed_waxwing", "seed_waxwing"),
    ("seed_blue_jay", "seed_hawk", "seed_blue_jay"),
]


class Command(BaseCommand):
    help = "Create synthetic bird friendships for local development."

    def handle(self, *args, **options):

        # Restrict execution to the development environment.
        if (
            not settings.DEBUG
            or settings.SETTINGS_MODULE != "config.settings.development"
        ):
            raise CommandError(
                "This command can only run with the "
                "development settings module and DEBUG=True."
            )

        created_active = 0
        created_ended = 0
        existing_friendships = 0

        # Roll back every change if any operation fails.
        with transaction.atomic():

            # Find the group created by seed_players.py.
            try:
                seed_group = Group.objects.get(
                    name=SEED_GROUP_NAME,
                )
            except Group.DoesNotExist:
                raise CommandError(
                    "Seed group does not exist. "
                    "Run seed_players first."
                )

            # Collect all synthetic player handles referenced
            # by our active and historical friendship lists.
            seed_handles = set()

            for first_handle, second_handle in ACTIVE_FRIENDSHIPS:
                seed_handles.add(first_handle)
                seed_handles.add(second_handle)

            for first_handle, second_handle, ended_by in ENDED_FRIENDSHIPS:
                seed_handles.add(first_handle)
                seed_handles.add(second_handle)
                seed_handles.add(ended_by)

            # Look up players and verify they belong to the
            # synthetic user group.
            players_by_handle = {}

            for handle in sorted(seed_handles):

                player = (
                    Player.objects
                    .select_related("user")
                    .filter(handle=handle)
                    .first()
                )

                if player is None:
                    raise CommandError(
                        f"Missing seed player: {handle}. "
                        "Run seed_players first."
                    )

                if player.user is None:
                    raise CommandError(
                        f"Seed player has no linked user: {handle}"
                    )

                if player.user.username != handle:
                    raise CommandError(
                        f"Username mismatch for seed player: {handle}"
                    )

                if not player.user.groups.filter(
                    pk=seed_group.pk,
                ).exists():
                    raise CommandError(
                        f"Player is not marked as seed data: {handle}"
                    )

                players_by_handle[handle] = player

            # Record the intended friendship pairs to guard
            # against accidental duplicates in our definitions.
            defined_pairs = set()

            # Create active friendships.
            for first_handle, second_handle in ACTIVE_FRIENDSHIPS:

                first_player = players_by_handle[first_handle]
                second_player = players_by_handle[second_handle]

                if first_player.pk == second_player.pk:
                    raise CommandError(
                        "A player cannot be friends with themselves."
                    )

                # The Friendship model requires player_a.pk
                # to be smaller than player_b.pk.
                player_a, player_b = sorted(
                    [first_player, second_player],
                    key=lambda player: player.pk,
                )

                pair_key = (player_a.pk, player_b.pk)

                if pair_key in defined_pairs:
                    raise CommandError(
                        f"Duplicate friendship definition: "
                        f"{first_handle}, {second_handle}"
                    )

                defined_pairs.add(pair_key)

                # Preserve existing friendships.
                #
                # We refuse to silently reactivate an ended
                # friendship during subsequent seed runs.
                existing = Friendship.objects.filter(
                    player_a=player_a,
                    player_b=player_b,
                )

                if existing.exists():

                    if not existing.filter(
                        ended_at__isnull=True,
                    ).exists():
                        raise CommandError(
                            f"Expected active friendship is ended: "
                            f"{first_handle}, {second_handle}"
                        )

                    existing_friendships += 1
                    continue

                Friendship.objects.create(
                    player_a=player_a,
                    player_b=player_b,
                )

                created_active += 1

            # Create historical ended friendships.
            for (
                first_handle,
                second_handle,
                ended_by_handle,
            ) in ENDED_FRIENDSHIPS:

                first_player = players_by_handle[first_handle]
                second_player = players_by_handle[second_handle]
                ending_player = players_by_handle[ended_by_handle]

                if first_player.pk == second_player.pk:
                    raise CommandError(
                        "A player cannot be friends with themselves."
                    )

                if ending_player.pk not in (
                    first_player.pk,
                    second_player.pk,
                ):
                    raise CommandError(
                        "The ending player must be a participant "
                        "in the friendship."
                    )

                player_a, player_b = sorted(
                    [first_player, second_player],
                    key=lambda player: player.pk,
                )

                pair_key = (player_a.pk, player_b.pk)

                if pair_key in defined_pairs:
                    raise CommandError(
                        f"Duplicate friendship definition: "
                        f"{first_handle}, {second_handle}"
                    )

                defined_pairs.add(pair_key)

                existing = Friendship.objects.filter(
                    player_a=player_a,
                    player_b=player_b,
                )

                if existing.exists():

                    # If an active friendship already exists,
                    # do not terminate it automatically.
                    if existing.filter(
                        ended_at__isnull=True,
                    ).exists():
                        raise CommandError(
                            f"Expected ended friendship is active: "
                            f"{first_handle}, {second_handle}"
                        )

                    existing_friendships += 1
                    continue

                # First create the friendship so Django
                # populates established_at automatically.
                friendship = Friendship.objects.create(
                    player_a=player_a,
                    player_b=player_b,
                )

                # End the friendship after its creation.
                friendship.ended_at = timezone.now()
                friendship.ended_by_player = ending_player

                friendship.save(
                    update_fields=[
                        "ended_at",
                        "ended_by_player",
                    ]
                )

                created_ended += 1

        self.stdout.write(
            self.style.SUCCESS(
                "Synthetic friendship seeding completed successfully."
            )
        )

        self.stdout.write(
            f"Active friendships created: {created_active}"
        )

        self.stdout.write(
            f"Ended friendships created: {created_ended}"
        )

        self.stdout.write(
            f"Existing friendships preserved: {existing_friendships}"
        )
