from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction

from ..models import Player


User = get_user_model()


class PlayerAlreadyClaimedError(Exception):
    """Raised when an existing Player is claimed before registration completes."""


class PlayerNameUnavailableError(Exception):
    """Raised when a requested new Player name is no longer available."""


@transaction.atomic
def create_registration(
    *,
    first_name: str,
    last_name: str,
    username: str,
    email: str,
    password: str,
    existing_player: Player | None,
    new_player_name: str,
) -> User:
    user = User.objects.create_user(
        first_name=first_name,
        last_name=last_name,
        username=username,
        email=email,
        password=password,
        is_active=False,
    )

    if existing_player is not None:
        player = (
            Player.objects
            .select_for_update()
            .get(pk=existing_player.pk)
        )

        if player.user_id is not None:
            raise PlayerAlreadyClaimedError(
                "This player has already been linked to another account."
            )

        player.user = user
        player.save(
            update_fields=["user"],
        )

    else:
        try:
            Player.objects.create(
                name=new_player_name,
                user=user,
            )
        except IntegrityError as error:
            raise PlayerNameUnavailableError(
                "This player name is no longer available."
            ) from error

    return user