from django.urls import path

from . import views

app_name = "portal"

urlpatterns = [
    path("", views.home, name="home"),
    path("games/", views.game_history, name="game_history"),
    path("games/add/", views.GameCreateView.as_view(), name="game-create"),
    path("players/overview/", views.player_overview, name="player-overview"),
]