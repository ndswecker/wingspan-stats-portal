from django.shortcuts import render
from .models import Game, GameResult

# Create your views here.
def game_history(request):
    games = (
        Game.objects
        .prefetch_related("results__player")
        .order_by("-date_played", "-id")[:25]
    )

    game_rows = []
    for game in games:
        results = list(game.results.all())
        game_rows.append({
            "id": game.id,
            "date_played": game.date_played,
            "player_one": results[0],
            "player_two": results[1],
        })

    return render(
        request, 
        "portal/game_history.html", 
        {"game_rows": game_rows}
    )
