from django.contrib import admin
from .models import Player, Game, GameResult

class GameResultInline(admin.TabularInline):
    model = GameResult
    extra = 0

@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)

@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ("id", "date_played", "human_player_mode",)
    list_filter = ("date_played", "human_player_mode")
    date_hierarchy = "date_played"
    inlines = [GameResultInline]

@admin.register(GameResult)
class GameResultAdmin(admin.ModelAdmin):
    list_display = ("game", "player", "turn_order", "score")
    list_filter = ("game", "player")
    search_fields = ("player__name",)
