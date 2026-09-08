from django.db import transaction
from django.utils import timezone

from ..models import (
    Friendship,
    FriendRequest,
    FriendRequestStatus,
    Player,
)

class FriendshipError(Exception):
    """Raised when a frienship operation violates a business rule."""


@transaction.atomic
def send_friend_request(
    *,
    requestor: Player,
    requestee: Player,
) -> FriendRequest:
    """Create a pending friend request between two Players."""
    if requestor.pk == requestee.pk:
        raise FriendshipError("You cannot send a friend request to yourself.")

    player_a_id = min(requestor.pk, requestee.pk)
    player_b_id = max(requestor.pk, requestee.pk)

    friendship_exists = Friendship.objects.filter(
        player_a_id=player_a_id,
        player_b_id=player_b_id,
        ended_at__isnull=True,
    ).exists()

    if friendship_exists:
        raise FriendshipError("You are already friends with this player.")

    outgoing_request_exists = FriendRequest.objects.filter(
        requestor=requestor,
        requestee=requestee,
        status=FriendRequestStatus.PENDING,
    ).exists()

    if outgoing_request_exists:
        raise FriendshipError("You already have a pending friend request to this player.")

    incoming_request_exists = FriendRequest.objects.filter(
        requestor=requestee,
        requestee=requestor,
        status=FriendRequestStatus.PENDING
    ).exists()

    if incoming_request_exists:
        raise FriendshipError("The player has already sent you a friend request.")

    friend_request = FriendRequest.objects.create(
        requestor=requestor,
        requestee=requestee,
        status=FriendRequestStatus.PENDING,
    )

    return friend_request


@transaction.atomic
def accept_friend_request(
    *,
    friend_request: FriendRequest,
    acting_player: Player,
) -> Friendship:
    """Accept a pending friend request and create an active Friendship"""

    # Reload and lock the FriendRequest row so its current state cannot be
    # changed by another transaction until this transaction completes.
    friend_request = (
        FriendRequest.objects
        .select_for_update()
        .get(pk=friend_request.pk)
    )

    if acting_player.pk != friend_request.requestee_id:
        raise FriendshipError("Only the player who received this request can accept it")

    if friend_request.status != FriendRequestStatus.PENDING:
        raise FriendshipError("This friend request is no longer pending.")

    player_a_id = min(friend_request.requestor_id, friend_request.requestee_id)
    player_b_id = max(friend_request.requestor_id, friend_request.requestee_id)

    friendship_exists = Friendship.objects.filter(
        player_a_id=player_a_id,
        player_b_id=player_b_id,
        ended_at__isnull=True,
    ).exists()

    if friendship_exists:
        raise FriendshipError("These players are already friends")

    friendship = Friendship.objects.create(
        player_a_id=player_a_id,
        player_b_id=player_b_id,
    )

    friend_request.status = FriendRequestStatus.ACCEPTED
    friend_request.resolved_at = timezone.now()
    friend_request.save(
        update_fields=[
            "status",
            "resolved_at",
        ]
    )

    return friendship

def get_player_by_handle(
    *,
    handle: str,
) -> Player | None:
    """Return the active Player matching the handle."""
    return Player.objects.filter(
        handle=handle,
        is_active=True,
    ).first()


def get_friends_for_player(
    *,
    player: Player,
) -> list[Player]:
    """Return the Player's current friends."""
    friendships = (
        Friendship.objects
        .filter(
            Q(player_a=player) | Q(player_b=player),
            ended_at__isnull=True,
        )
        .select_related(
            "player_a",
            "player_b",
        )
    )

    friends = []

    for friendship in friendships:
        if friendship.player_a_id == player.pk:
            friends.append(friendship.player_b)
        else:
            friends.append(friendship.player_a)

    return friends


def get_pending_incoming_requests(
    *,
    player: Player,
):
    """Return pending friend requests received by the Player."""
    return (
        FriendRequest.objects
        .filter(
            requestee=player,
            status=FriendRequestStatus.PENDING,
        )
        .select_related("requestor")
        .order_by("-requested_at")
    )


def get_pending_outgoing_requests(
    *,
    player: Player,
):
    """Return pending friend requests sent by the Player."""
    return (
        FriendRequest.objects
        .filter(
            requestor=player,
            status=FriendRequestStatus.PENDING,
        )
        .select_related("requestee")
        .order_by("-requested_at")
    )