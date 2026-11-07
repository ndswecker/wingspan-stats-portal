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


def get_public_players():
    """
    Return all active Players who have opted into public visibility.

    The results are independent of the requesting user's
    authentication status, friendships, or administrative privileges.
    """

    # Only active Players with public profiles are eligible.
    public_players = Player.objects.filter(
        is_active=True,
        is_public=True,
    )

    # Sort alphabetically for consistent ordering.
    public_players = public_players.order_by("name")

    return public_players


def get_friends_leaderboard_players(
    *,
    user,
):
    """
    Return the Players eligible for a user's Friends leaderboard.

    Eligible Players include:
        - The authenticated user's own Player
        - Their active friends, regardless of public/private status

    Inactive Players and former friends are excluded.

    Staff and superusers receive no special access.
    Anonymous users and users without a linked Player
    receive an empty queryset.
    """

    # Anonymous users cannot access a Friends leaderboard.
    if not user.is_authenticated:
        return Player.objects.none()

    # Identify the Player associated with the authenticated user.
    acting_player = getattr(user, "player", None)

    # Users without a linked Player cannot access a Friends leaderboard.
    if acting_player is None:
        return Player.objects.none()

    # Find active friendships where the acting player
    # occupies the player_a position.
    friend_ids = Friendship.objects.filter(
        ended_at__isnull=True,
        player_a=acting_player,
    ).values("player_b_id")

    # Find active friendships where the acting player
    # occupies the player_b position.
    reverse_friend_ids = Friendship.objects.filter(
        ended_at__isnull=True,
        player_b=acting_player,
    ).values("player_a_id")

    # A Player qualifies if they are the acting player
    # or an active friend.
    #
    # Public visibility is intentionally not considered.
    friendship_conditions = (
        Q(pk=acting_player.pk)
        | Q(pk__in=friend_ids)
        | Q(pk__in=reverse_friend_ids)
    )

    # Exclude inactive Players.
    leaderboard_players = Player.objects.filter(
        is_active=True,
    )

    # Apply the friendship conditions.
    leaderboard_players = leaderboard_players.filter(
        friendship_conditions,
    )

    # Sort alphabetically for consistent ordering.
    leaderboard_players = leaderboard_players.order_by("name")

    return leaderboard_players
    