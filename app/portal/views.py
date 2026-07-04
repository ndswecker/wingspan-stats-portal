from datetime import date
from django.shortcuts import render
from .models import Game, GameResult

# Create your views here.
def game_history(request):
    view_mode = request.GET.get("view", "month")


    available_months = list(
        Game.objects.dates("date_played", "month", order="DESC")
    )
    latetest_month = available_months[0] if available_months else None

    if view_mode == "all":
        current_month = None
        previous_month = None
        next_month = None

        games = (
            Game.objects
            .prefetch_related("results__player")
            .order_by("-date_played", "-id")
        )
    else:
        selected_month = request.GET.get("month")

        if selected_month:
            year, month = selected_month.split("-")
            current_month = date(int(year), int(month), 1)
        else:
            current_month = available_months[0]

        current_index = available_months.index(current_month)

        if current_index - 1 >= 0:
            next_month = available_months[current_index - 1]
        else:
            next_month = None

        if current_index + 1 < len(available_months):
            previous_month = available_months[current_index + 1]
        else:
            previous_month = None

        games = (
            Game.objects
            .prefetch_related("results__player")
            .filter(
                date_played__year=current_month.year,
                date_played__month=current_month.month
            )
            .order_by("-date_played", "-id")
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
            "date_played": game.date_played,
            "player_one": player_one,
            "player_two": player_two,
            "winner": winner,
            "row_class": row_class
        })

    return render(
        request, 
        "portal/game_history.html", 
        {
            "game_rows": game_rows,
            "view_mode": view_mode,
            "current_month": current_month,
            "previous_month": previous_month,
            "next_month": next_month,
            "latetest_month": latetest_month,
        }
    )
