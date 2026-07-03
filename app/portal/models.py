from django.db import models

# Create your models here.
class Player(models.Model):
    name = models.CharField(
        max_length=50,
        unique=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
    
class Game(models.Model):
    date_played = models.DateField()

    class Meta:
        ordering = ["-date_played", "-id"]

    def __str__(self):
        return f"Game {self.id} - {self.date_played}"
    
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