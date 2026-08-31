from django.contrib import admin
from .models import Player, Game, GameResult

class GameResultInline(admin.TabularInline):
    model = GameResult
    extra = 0

@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = (
        "name", 
        "username",
        "email",
        "is_active"
    )
    list_filter = ("is_active",)
    search_fields = (
        "name",
        "user__username",
        "user__email",
    )
    list_select_related = ("user",)

    @admin.display(description="Username")
    def username(self, obj):
        if obj.user is None:
            return "—"

        return obj.user.username

    @admin.display(description="Email")
    def email(self, obj):
        if obj.user is None:
            return "—"

        return obj.user.email

@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ("id", "date_played", "human_player_mode",)
    list_filter = ("date_played", "human_player_mode")
    date_hierarchy = "date_played"
    inlines = [GameResultInline]

@admin.register(GameResult)
class GameResultAdmin(admin.ModelAdmin):
    list_display = (
        "is_confirmed",
        "game__date_played",
        "game__mode",
        "game__id",
        "player", 
        "turn_order", 
        "score",
    )
    list_filter = ("game__date_played", "game__human_player_mode", "player", "is_confirmed")
    search_fields = ("player__name", "player__user__username", "player__user__email")
    date_hierarchy = "game__date_played"

    @admin.display(description="Game Type")
    def game__mode(self, obj):
        return obj.game.get_human_player_mode_display()