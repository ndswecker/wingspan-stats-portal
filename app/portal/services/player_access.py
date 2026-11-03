from django.db.models import Q

from ..models import Player, Friendship, GameResult


def get_viewable_players(
    *,
    user,
):
    """
    Return the Players whose statistics the user may view.

    Regular users may view:
        - Their own Player
        - Active friends
        - Public Players

    Staff and superusers may view all Players.

    Anonymous users may not view any Players.
    """   

    # Anonymous users cannot access player statistics
    if not user.is_authenticated:
        return Player.objects.none()

    # Staff and superusers can view all players
    if user.is_staff or user.is_superuser:
        return Player.objects.all()

    # Identify the Player associated with the authenticated user
    acting_player = getattr(user, "player", None)

    # Authenticated users without a linked Player cannot view any players
    if acting_player is None:
        return Player.objects.none()

    # Find active friendships where the acting player is in the 'a' position
    friend_ids = Friendship.objects.filter(
        ended_at__isnull=True,
        player_a=acting_player,
    ).values("player_b_id")

    # Find all the active friendships where the acting player is in the 'b' position
    reverse_friend_ids = Friendship.objects.filter(
        ended_at__isnull=True,
        player_b=acting_player,
    ).values("player_a_id")

    # Conditions for a viewable player:
    #   1. The acting player
    #   2. An active friend
    #   3. A public player
    visibility_conditions = (
        Q(pk=acting_player.pk)
        | Q(pk__in=friend_ids)
        | Q(pk__in=reverse_friend_ids)
        | Q(is_public=True)
    )

    viewable_players = Player.objects.filter(
        is_active=True,
    )

    viewable_players = viewable_players.filter(
        visibility_conditions,
    )

    viewable_players = viewable_players.order_by("name")

    return viewable_players


def can_view_game(*, user, game):
    """
    Determine whether a user may view a game's full details.

    Access is granted to:
        - Staff and superusers
        - Players who participated in the game

    Friendship and public visibility do not grant access
    to the full Game Detail page.
    """

    # Anonymous users cannot view game details.
    if not user.is_authenticated:
        return False

    # Staff and superusers can inspect all games.
    if user.is_staff or user.is_superuser:
        return True

    # Identify the Player associated with the user.
    acting_player = getattr(user, "player", None)

    if acting_player is None:
        return False

    # Check whether the player participated in this game.
    is_participant = GameResult.objects.filter(
        game=game,
        player=acting_player,
    ).exists()

    return is_participant



    