from django.shortcuts import render

from ..services.dashboard import (
    get_player_performance_summary,
    get_total_games_played,
)


def home(request):
    total_games_played = get_total_games_played()

    context = {
        "total_games_played": total_games_played,
        "player_performance_summary": get_player_performance_summary(),
    }

    return render(request, "portal/home.html", context)