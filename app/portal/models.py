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

    is_public = models.BooleanField(
        default=False,
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


class Achievement(models.Model):
    code = models.CharField(
        max_length=100,
        unique=True,
    )

    name = models.CharField(
        max_length=100,
    )

    description = models.TextField()

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class PlayerAchievement(models.Model):
    player = models.ForeignKey(
        Player,
        on_delete=models.CASCADE,
        related_name="achievements",
    )

    achievement = models.ForeignKey(
        Achievement,
        on_delete=models.PROTECT,
        related_name="player_awards",
    )

    source_result = models.ForeignKey(
        GameResult,
        on_delete=models.CASCADE,
        related_name="achievements",
        null=True,
        blank=True,
    )

    # Applicable period for recurring achievements.
    # period_end is exclusive.
    # Both fields remain NULL for per-game achievements.
    period_start = models.DateField(
        null=True,
        blank=True,
    )

    period_end = models.DateField(
        null=True,
        blank=True,
    )

    awarded_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-awarded_at"]

        constraints = [
            # Prevent duplicate awards for the same game result.
            models.UniqueConstraint(
                fields=[
                    "achievement",
                    "source_result",
                ],
                name="unique_achievement_per_result",
            ),

            # Prevent the same player from earning the same
            # recurring achievement twice for one period.
            models.UniqueConstraint(
                fields=[
                    "player",
                    "achievement",
                    "period_start",
                ],
                condition=models.Q(
                    period_start__isnull=False,
                ),
                name="unique_player_achievement_per_period",
            ),

            # Per-game awards use source_result.
            # Recurring awards use period_start and period_end.
            models.CheckConstraint(
                condition=(
                    models.Q(
                        source_result__isnull=False,
                        period_start__isnull=True,
                        period_end__isnull=True,
                    )
                    |
                    models.Q(
                        source_result__isnull=True,
                        period_start__isnull=False,
                        period_end__isnull=False,
                    )
                ),
                name="valid_achievement_source_or_period",
            ),

            # The end of a recurring period must be after its start.
            models.CheckConstraint(
                condition=(
                    models.Q(period_start__isnull=True)
                    |
                    models.Q(
                        period_end__gt=models.F("period_start"),
                    )
                ),
                name="valid_achievement_period_dates",
            ),
        ]

    def __str__(self):
        return (
            f"{self.player} - "
            f"{self.achievement.name}"
        )