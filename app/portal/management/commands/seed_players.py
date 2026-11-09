
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from ...models import Player


# All synthetic users belong to this group.
# This gives future seed and cleanup commands a reliable
# way to identify our development accounts.
SEED_GROUP_NAME = "wingspan_seed_data"

# Shared password for local development accounts only.
SEED_USER_PASSWORD = "WingspanTest2026!"


# Each entry contains:
# (player name, username/handle, public visibility)
SEED_PLAYERS = [
    ("American Kestrel", "seed_kestrel", True),
    ("Barn Owl", "seed_barn_owl", True),
    ("Blue Jay", "seed_blue_jay", False),
    ("Cedar Waxwing", "seed_waxwing", True),
    ("Dark-eyed Junco", "seed_junco", False),
    ("Great Blue Heron", "seed_heron", True),
    ("House Finch", "seed_finch", True),
    ("Killdeer", "seed_killdeer", False),
    ("Mountain Chickadee", "seed_chickadee", True),
    ("Northern Flicker", "seed_flicker", True),
    ("Osprey", "seed_osprey", False),
    ("Red-tailed Hawk", "seed_hawk", True),
    ("Snowy Egret", "seed_egret", False),
    ("Tree Swallow", "seed_swallow", True),
    ("Western Tanager", "seed_tanager", False),
]


class Command(BaseCommand):
    help = "Create synthetic bird users and players for local development."

    def handle(self, *args, **options):

        # Restrict execution to the Django development settings.
        if (
            not settings.DEBUG
            or settings.SETTINGS_MODULE != "config.settings.development"
        ):
            raise CommandError(
                "This command can only run with the "
                "development settings module and DEBUG=True."
            )

        User = get_user_model()

        created_users = 0
        created_players = 0
        existing_players = 0

        # All database changes are committed together.
        # Any failure rolls back the entire operation.
        with transaction.atomic():

            seed_group, _ = Group.objects.get_or_create(
                name=SEED_GROUP_NAME,
            )

            for name, handle, is_public in SEED_PLAYERS:

                # Check whether the username already exists.
                user = User.objects.filter(
                    username=handle,
                ).first()

                if user is not None:

                    # Do not adopt an unrelated account.
                    if not user.groups.filter(
                        pk=seed_group.pk,
                    ).exists():
                        raise CommandError(
                            f"Username collision: {handle}. "
                            "The existing account is not seed data."
                        )

                    # Confirm that the existing user is linked
                    # to the expected synthetic Player.
                    player = Player.objects.filter(
                        user=user,
                    ).first()

                    if (
                        player is None
                        or player.handle != handle
                        or player.name != name
                    ):
                        raise CommandError(
                            f"Seed player relationship mismatch: {handle}"
                        )

                    # Preserve existing test records, including
                    # their passwords and privacy settings.
                    existing_players += 1
                    continue

                # Prevent conflicts with real Player records.
                if Player.objects.filter(handle=handle).exists():
                    raise CommandError(
                        f"Player handle already exists: {handle}"
                    )

                if Player.objects.filter(name=name).exists():
                    raise CommandError(
                        f"Player name already exists: {name}"
                    )

                # Create a normal Django User account.
                # create_user securely hashes the password.
                user = User.objects.create_user(
                    username=handle,
                    password=SEED_USER_PASSWORD,
                )

                # Explicitly prevent administrative privileges.
                user.is_active = True
                user.is_staff = False
                user.is_superuser = False
                user.save()

                # Mark this user as synthetic development data.
                user.groups.add(seed_group)

                created_users += 1

                # Create the corresponding Player record.
                Player.objects.create(
                    user=user,
                    name=name,
                    handle=handle,
                    is_active=True,
                    is_public=is_public,
                )

                created_players += 1

        self.stdout.write(
            self.style.SUCCESS(
                "Synthetic player seeding completed successfully."
            )
        )

        self.stdout.write(f"Users created: {created_users}")
        self.stdout.write(f"Players created: {created_players}")
        self.stdout.write(f"Existing players preserved: {existing_players}")
