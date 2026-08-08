from datetime import date
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render
from django.views import View

from .models import Game, GameResult

from .forms import (
    GameForm, 
    GameResultFormSet,
    PlayerStatisticsFilterForm,
    PlayerScoreTrendsFilterForm,
)

from .services.game_entry import create_game
from .services.dashboard import (get_player_performance_summary, get_total_games_played,)
from .services.game_result_selection import select_game_results
from .services.player_general_stats import calculate_general_stats
from .services.player_score_trends import (
    calculate_monthly_score_averages,
    resolve_score_trend_period,
)
from .services.player_score_trend_chart import (
    build_monthly_score_chart,
    build_monthly_score_comparison_chart,
)

from .services.player_score_distribution import (
    calculate_score_distribution,
)

from .services.player_score_distribution_chart import (
    build_score_distribution_chart,
)
from .services.player_score_trends import (
    calculate_monthly_score_averages,
    compare_monthly_score_averages,
    resolve_score_trend_period,
)

def get_available_months():
    """Returns a list of available months for which games have been played."""
    return list(
        Game.objects
        .filter(human_player_mode=Game.HumanPlayerMode.MULTIPLE)
        .dates("date_played", "month", order="DESC")
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
            .filter(human_player_mode=Game.HumanPlayerMode.MULTIPLE,)
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
                human_player_mode=Game.HumanPlayerMode.MULTIPLE,
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

def home(request):
    total_games_played = get_total_games_played()
    context = {
        "total_games_played": total_games_played,
        "player_performance_summary": get_player_performance_summary(),
    }
    return render(request, "portal/home.html", context)

class StaffRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.is_staff:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
    
class GameCreateView(StaffRequiredMixin, View):
    template_name = "portal/game_create.html"

    def get(self, request):
        game_form = GameForm()

        result_formset = GameResultFormSet(
            prefix="results",
        )

        context = {
            "game_form": game_form,
            "result_formset": result_formset,
        }

        return render(
            request,
            self.template_name,
            context,
        )
    
    def post(self, request):
        game_form = GameForm(request.POST)

        game_form_is_valid = game_form.is_valid()

        human_player_mode = request.POST.get("human_player_mode")

        if game_form_is_valid:
            human_player_mode = game_form.cleaned_data["human_player_mode"]

        result_formset = GameResultFormSet(
            request.POST,
            prefix="results",
            human_player_mode=human_player_mode,
        )

        result_formset_is_valid = result_formset.is_valid()

        if game_form_is_valid and result_formset_is_valid:
            game = create_game(
                game_data=game_form.cleaned_data,
                result_forms=result_formset.forms,
            )

            messages.success(
                request,
                f"Game {game.id} was added successfully.",
            )

            return redirect("portal:game-create")

        context = {
            "game_form": game_form,
            "result_formset": result_formset,
        }

        return render(
            request,
            self.template_name,
            context,
        )

def player_overview(request):
    filter_form = PlayerStatisticsFilterForm(
        request.GET or None,
    )

    general_stats = None
    selected_player = None
    selected_game_type_label = None

    if filter_form.is_valid():
        selected_player = filter_form.cleaned_data["player"]

        game_type = Game.HumanPlayerMode(
            filter_form.cleaned_data["game_type"],
        )
        selected_game_type_label = game_type.label

        game_results = select_game_results(
            player=selected_player,
            game_type=game_type,
        )

        general_stats = calculate_general_stats(
            game_results=game_results,
        )

    context = {
        "filter_form": filter_form,
        "selected_player": selected_player,
        "selected_game_type_label": selected_game_type_label,
        "general_stats": general_stats,
    }

    return render(
        request,
        "portal/player_overview.html",
        context,
    )

def player_score_trends(request):
    filter_form = PlayerScoreTrendsFilterForm(
        request.GET or None,
    )

    selected_player = None
    selected_secondary_player = None
    selected_game_type_label = None

    is_comparison = False

    selected_period_label = None

    monthly_scores = None
    monthly_chart_html = None

    secondary_monthly_scores = None
    monthly_comparisons = None

    score_distribution = None
    distribution_chart_html = None

    has_results = False

    if filter_form.is_valid():
        selected_player = filter_form.cleaned_data["player"]
        selected_secondary_player = filter_form.cleaned_data["secondary_player"]
        is_comparison = selected_secondary_player is not None

        game_type = Game.HumanPlayerMode(
            filter_form.cleaned_data["game_type"],
        )
        selected_game_type_label = game_type.label

        period = resolve_score_trend_period(
            selected_period=filter_form.cleaned_data["period"],
        )
        selected_period_label = period.label

        game_results = select_game_results(
            player=selected_player,
            game_type=game_type,
            start_date=period.start_date,
            end_date=period.end_date,
        )

        secondary_game_results = None

        if is_comparison:
            secondary_game_results = select_game_results(
                player=selected_secondary_player,
                game_type=game_type,
                start_date=period.start_date,
                end_date=period.end_date,
            )

        has_results = game_results.exists()

        if has_results:

            monthly_scores = calculate_monthly_score_averages(
                game_results=game_results,
                start_date=period.start_date,
                end_date=period.end_date,
            )

            if is_comparison:
                secondary_monthly_scores = calculate_monthly_score_averages(
                    game_results=secondary_game_results,
                    start_date=period.start_date,
                    end_date=period.end_date,
                )

                monthly_comparisons = compare_monthly_score_averages(
                    primary_monthly_scores=monthly_scores,
                    secondary_monthly_scores=secondary_monthly_scores,
                )

            score_distribution = calculate_score_distribution(
                game_results=game_results,
            )

            if is_comparison:
                monthly_figure = build_monthly_score_comparison_chart(
                    primary_monthly_scores=monthly_scores,
                    secondary_monthly_scores=secondary_monthly_scores,
                    primary_player=selected_player,
                    secondary_player=selected_secondary_player,
                    game_type_label=selected_game_type_label,
                    period_label=selected_period_label,
                )
            else:
                monthly_figure = build_monthly_score_chart(
                    monthly_scores=monthly_scores,
                    player=selected_player,
                    game_type_label=selected_game_type_label,
                    period_label=selected_period_label,
                )

            distribution_figure = build_score_distribution_chart(
                score_distribution=score_distribution,
            )

            monthly_chart_html = monthly_figure.to_html(
                full_html=False,
                include_plotlyjs="cdn",
                config={
                    "responsive": True,
                    "displaylogo": False,
                    "displayModeBar": False,
                    "scrollZoom": False,
                    "doubleClick": False,
                },
            )

            distribution_chart_html = distribution_figure.to_html(
                full_html=False,
                include_plotlyjs=False,
                config={
                    "responsive": True,
                    "displaylogo": False,
                    "displayModeBar": False,
                    "scrollZoom": False,
                    "doubleClick": False,
                },
            )

    context = {
        "filter_form": filter_form,
        "selected_player": selected_player,
        "selected_secondary_player": selected_secondary_player,
        "is_comparison": is_comparison,
        "selected_game_type_label": selected_game_type_label,
        "selected_period_label": selected_period_label,


        "monthly_scores": monthly_scores,
        "secondary_monthly_scores": secondary_monthly_scores,
        "monthly_comparisons": monthly_comparisons,

        "monthly_chart_html": monthly_chart_html,
        "score_distribution": score_distribution,
        "distribution_chart_html": distribution_chart_html,
        "has_results": has_results,
    }

    return render(
        request,
        "portal/player_score_trends.html",
        context,
    )