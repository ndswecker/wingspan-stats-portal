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
    previous_date = None
    date_group_index = 0
    for game in games:
        results = list(game.results.order_by("player__name"))

        player_one = results[0]
        player_two = results[1]

        if player_one.score > player_two.score:
            winner = player_one
        elif player_two.score > player_one.score:
            winner = player_two
        else:
            winner = None

        if game.date_played != previous_date:
            date_group_index += 1
            previous_date = game.date_played
        row_class = "table-light" if date_group_index % 2 == 0 else ""

        game_rows.append({
            "id": game.id,
            "date_played": game.date_played,
            "player_one": player_one,
            "player_two": player_two,
            "winner": winner,
            "row_class": row_class
        })

    return render(
        request, 
        "portal/game_history.html", 
        {"game_rows": game_rows}
    )
