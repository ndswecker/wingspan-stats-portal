from datetime import date
from django.shortcuts import render
from .models import Game, GameResult

def get_available_months():
    """Returns a list of available months for which games have been played."""
    return list(
        Game.objects.dates("date_played", "month", order="DESC")
    )

def get_game_history_context(request, months_with_games):
    """Returns the games and month navigation context for the game history view."""
    view_mode = request.GET.get("view", "month")
    latest_month = months_with_games[0] if months_with_games else None

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
            current_month = months_with_games[0]

        current_index = months_with_games.index(current_month)

        if current_index - 1 >= 0:
            next_month = months_with_games[current_index - 1]
        else:
            next_month = None

        if current_index + 1 < len(months_with_games):
            previous_month = months_with_games[current_index + 1]
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

    return {
        "games": games,
        "view_mode": view_mode,
        "current_month": current_month,
        "previous_month": previous_month,
        "next_month": next_month,
        "latest_month": latest_month,
    }

def calculate_night_winners(games):
    """ Calculate the winner for each game night.
    
    Games are grouped by date. The night winner is determined first by most
    individual wins, and then by highest total points if the gme wins are tied."""
    night_stats = {}

    for game in games:
        results = list(game.results.order_by("player__name"))

        if len(results) != 2:
            continue

        player_one = results[0]
        player_two = results[1]

        # Create stats containers for this game night if this is the first game of the night
        if game.date_played not in night_stats:
            night_stats[game.date_played] = {
                "game_wins": {},
                "total_points": {},
            }
        
        # Update each players cumulative score for the night
        for result in results:
            player = result.player

            if player not in night_stats[game.date_played]["game_wins"]:
                night_stats[game.date_played]["game_wins"][player] = 0
            if player not in night_stats[game.date_played]["total_points"]:
                night_stats[game.date_played]["total_points"][player] = 0
            
            night_stats[game.date_played]["total_points"][player] += result.score

        # Record the winner of this individual game.
        if player_one.score > player_two.score:
            night_stats[game.date_played]["game_wins"][player_one.player] += 1
        elif player_two.score > player_one.score:
            night_stats[game.date_played]["game_wins"][player_two.player] += 1

    # Determine the overall winner for each game night.
    night_winners = {}

    for date_played, stats in night_stats.items():
        players = list(stats["total_points"].keys())
        
        if len(players) != 2:
            night_winners[date_played] = None
            continue
        
        player_one = players[0]
        player_two = players[1]
        
        player_one_wins = stats["game_wins"][player_one]
        player_two_wins = stats["game_wins"][player_two]

        if player_one_wins > player_two_wins:
            night_winners[date_played] = player_one
        elif player_two_wins > player_one_wins:
            night_winners[date_played] = player_two
        else:
            player_one_points = stats["total_points"][player_one]
            player_two_points = stats["total_points"][player_two]

            if player_one_points > player_two_points:
                night_winners[date_played] = player_one
            elif player_two_points > player_one_points:
                night_winners[date_played] = player_two
            else:
                night_winners[date_played] = None
                
                
    return night_winners

def build_game_rows(games):
    """
    Build display rows for the game history table.
    Each row contains the game date, both player results, the game winner,
    night winner, and the row styling class used to visually group games by date.
    """

    games = list(games)
    night_winners = calculate_night_winners(games)
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


        is_new_date_group = game.date_played != previous_date

        if is_new_date_group:
            date_group_index += 1
            previous_date = game.date_played
        
        row_class = "table-light" if date_group_index % 2 == 0 else ""


        game_rows.append({
            "date_played": game.date_played,
            "player_one": player_one,
            "player_two": player_two,
            "winner": winner,
            "night_winner": night_winners.get(game.date_played),
            "row_class": row_class,
            "is_new_date_group": is_new_date_group,
        })

    return game_rows

def game_history(request):
    months_with_games = get_available_months()
    game_history_context = get_game_history_context(request, months_with_games)
    game_rows = build_game_rows(game_history_context["games"])

    context = {
        "game_rows": game_rows,
        "view_mode": game_history_context["view_mode"],
        "current_month": game_history_context["current_month"],
        "previous_month": game_history_context["previous_month"],
        "next_month": game_history_context["next_month"],
        "latest_month": game_history_context["latest_month"],
    }

    return render(request, "portal/game_history.html", context)

  