from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator

handle_validator = RegexValidator(
    regex=r"^[a-z][a-z0-9_]{2,31}$",
    message=(
        "Handle must be 3–32 characters, start with a lowercase letter, "
        "and contain only lowercase letters, numbers, and underscores."
    ),
)

# Create your models here.
class Player(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="player",
        null=True,
        blank=True,
    )

    name = models.CharField(
        max_length=50,
        unique=True,
    )

    handle = models.CharField(
        max_length=32,
        unique=True,
        validators=[handle_validator]
    )

    is_active = models.BooleanField(
        default=True,
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
    
class Game(models.Model):
    class HumanPlayerMode(models.TextChoices):
        SINGLE = "single_human", "Solo Game"
        MULTIPLE = "multi_human", "Competitive Game"

    date_played = models.DateField()

    human_player_mode = models.CharField(
        max_length=20,
        choices=HumanPlayerMode.choices,
    )

    class Meta:
        ordering = ["-date_played", "-id"]

    def __str__(self):
        return (
            f"Game {self.id} - "
            f"{self.date_played} - "
            f"{self.get_human_player_mode_display()}"
        )
    
class GameResult(models.Model):
    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        related_name="results",
    )

    player = models.ForeignKey(
        Player,
        on_delete=models.PROTECT,
        related_name="game_results",
    )

    turn_order = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
    )

    score = models.PositiveSmallIntegerField()

    is_confirmed = models.BooleanField(
        default=False,
    )

    class Meta:
        ordering = ["game", "-score", "player"]
        constraints = [
            models.UniqueConstraint(
                fields=["game", "player"],
                name="unique_player_per_game",
            ),
            models.UniqueConstraint(
                fields=["game", "turn_order"],
                name="unique_turn_order_per_game",
            )
        ]

    def __str__(self):
        return f"{self.game} - {self.player} - ({self.score})"

class Friendship(models.Model):
    player_a = models.ForeignKey(
        Player,
        on_delete=models.CASCADE,
        related_name="friendships_as_player_a"
    )

    player_b = models.ForeignKey(
        Player,
        on_delete=models.CASCADE,
        related_name="friendships_as_player_b"
    )

    established_at = models.DateTimeField(
        auto_now_add=True,
    )

    ended_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    ended_by_player = models.ForeignKey(
        Player,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="friendships_ended"
    )

    class Meta:
        ordering=["-established_at"]

        constraints = [
            models.CheckConstraint(
                condition=models.Q(player_a__lt=models.F("player_b")),
                name="friendship_canonical_player_order",
            ),

            models.UniqueConstraint(
                fields=["player_a", "player_b"],
                condition=models.Q(ended_at__isnull=True),
                name="friendship_one_active_per_pair",
            )
        ]

    def __str__(self):
        return (
            f"friendship between {self.player_a} and {self.player_b},"
            f"est. {self.established_at}, ended {self.ended_at}"
        )

class FriendRequestStatus(models.TextChoices):
    PENDING = "pending", "Pending Request"
    ACCEPTED = "accepted", "Accepted Request"
    DECLINED = "declined", "Declined Request"
    CANCELLED = "cancelled", "Cancelled Request"
class FriendRequest(models.Model):

    requested_at = models.DateTimeField(
        auto_now_add=True,
    )

    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=FriendRequestStatus.choices,
        default=FriendRequestStatus.PENDING,
    )

    requestor = models.ForeignKey(
        Player,
        on_delete=models.CASCADE,
        related_name="sent_friend_requests",
    )

    requestee = models.ForeignKey(
        Player,
        on_delete=models.CASCADE,
        related_name="received_friend_requests",
    )

    class Meta:
        ordering = ["-requested_at"]

        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(
                        status=FriendRequestStatus.PENDING,
                        resolved_at__isnull=True,
                    )
                    |
                    models.Q(
                        status__in=[
                            FriendRequestStatus.ACCEPTED,
                            FriendRequestStatus.DECLINED,
                            FriendRequestStatus.CANCELLED,
                        ],
                        resolved_at__isnull=False,
                    )
                ),
                name="friend_request_status_resolution_valid",
            ),
            models.CheckConstraint(
                condition=~models.Q(
                    requestor=models.F("requestee")
                ),
                name="friend_request_no_self_request"
            ),
        ]

    def __str__(self):
        return f"{self.requestor} requesting friendship with {self.requestee} with status of {self.status}"
