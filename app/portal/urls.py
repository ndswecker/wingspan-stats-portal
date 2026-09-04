from django.urls import path

from . import views

app_name = "portal"

urlpatterns = [
    path("", views.home, name="home"),
    path("games/", views.game_history, name="game_history"),
    path("games/add/", views.GameCreateView.as_view(), name="game-create"),
    path("players/overview/", views.player_overview, name="player-overview"),
    path("players/score-trends/", views.player_score_trends, name="player-score-trends"),
    path("account/", views.account, name="account"),
    path("register/", views.register, name="register"),
    path("games/<int:pk>/", views.game_detail, name="game-detail"),
    path("games/<int:pk>/edit/", views.game_edit, name="game-edit"),
]