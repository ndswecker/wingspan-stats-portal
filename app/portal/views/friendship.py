from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from ..models import (
    FriendRequest,
    Player,
)

from ..services.friendship import (
    get_friends_for_player,
    get_pending_incoming_requests,
    get_pending_outgoing_requests,
    get_player_by_handle,
    FriendshipError,
    send_friend_request,
    accept_friend_request,
    remove_friendship,
    cancel_friend_request,
    decline_friend_request,
)

@login_required
def friends(request):
    player = request.user.player

    friends = get_friends_for_player(
        player=player,
    )

    incoming_requests = get_pending_incoming_requests(
        player=player,
    )

    outgoing_requests = get_pending_outgoing_requests(
        player=player,
    )

    context = {
        "player": player,
        "friends": friends,
        "incoming_requests": incoming_requests,
        "outgoing_requests": outgoing_requests,
    }

    return render(
        request,
        "portal/friends.html",
        context,
    )

@login_required
@require_POST
def send_friend_request_view(request):
    player = request.user.player

    handle = request.POST.get(
        "handle",
        "",
    ).strip()

    if handle.startswith("@"):
        handle=handle[1:]

    requestee = get_player_by_handle(
        handle=handle,
    )

    if requestee is None:
        messages.error(
            request,
            "No player was found with that handle.",
        )

        return redirect("portal:friends")

    try:
        send_friend_request(
            requestor=player,
            requestee=requestee,
        )
    except FriendshipError as error:
        messages.error(
            request,
            str(error),
        )
    else:
        messages.success(
            request,
            f"Friend request sent to @{requestee.handle}.",
        )

    return redirect("portal:friends")

@login_required
@require_POST
def accept_friend_request_view(
    request,
    friend_request_id,
):
    player = request.user.player

    friend_request = get_object_or_404(
        FriendRequest,
        pk=friend_request_id,
    )

    try:
        accept_friend_request(
            friend_request=friend_request,
            acting_player=player,
        )
    except FriendshipError as error:
        messages.error(
            request,
            str(error),
        )
    else:
        messages.success(
            request,
            f"You are now friends with @{friend_request.requestor.handle}.",
        )

    return redirect("portal:friends")

@login_required
@require_POST
def remove_friend_view(
    request,
    player_id,
):
    acting_player = request.user.player

    other_player = get_object_or_404(
        Player,
        pk=player_id,
        is_active=True,
    )

    try:
        remove_friendship(
            acting_player=acting_player,
            other_player=other_player,
        )
    except FriendshipError as error:
        messages.error(
            request,
            str(error),
        )
    else:
        messages.success(
            request,
            f"@{other_player.handle} was removed from your friends.",
        )

    return redirect("portal:friends")

@login_required
@require_POST
def cancel_friend_request_view(
    request,
    friend_request_id,
):
    player = request.user.player

    friend_request = get_object_or_404(
        FriendRequest,
        pk=friend_request_id,
    )

    try:
        cancel_friend_request(
            friend_request=friend_request,
            acting_player=player,
        )
    except FriendshipError as error:
        messages.error(
            request,
            str(error),
        )
    else:
        messages.success(
            request,
            f"Friend request to @{friend_request.requestee.handle} was cancelled.",
        )

    return redirect("portal:friends")

@login_required
@require_POST
def decline_friend_request_view(
    request,
    friend_request_id,
):
    player = request.user.player

    friend_request = get_object_or_404(
        FriendRequest,
        pk=friend_request_id,
    )

    try:
        decline_friend_request(
            friend_request=friend_request,
            acting_player=player,
        )
    except FriendshipError as error:
        messages.error(
            request,
            str(error),
        )
    else:
        messages.success(
            request,
            f"Friend request from @{friend_request.requestor.handle} was declined.",
        )

    return redirect("portal:friends")