from django.urls import path

from . import views

app_name = "portal"

urlpatterns = [
    path("games/", views.game_history, name="game_history"),
]