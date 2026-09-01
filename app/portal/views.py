
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect, render

from .models import Game, GameResult

from .forms import (
    GameForm, 
    GameResultFormSet,
    PlayerStatisticsFilterForm,
    PlayerScoreTrendsFilterForm,
    RegistrationForm,
    PlayerGameHistoryFilterForm,
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
    calculate_score_distribution_comparison,
    compare_score_distributions,
)

from .services.player_score_distribution_chart import (
    build_score_distribution_chart,
    build_score_distribution_comparison_chart,
)
from .services.player_score_trends import (
    calculate_monthly_score_averages,
    compare_monthly_score_averages,
    resolve_score_trend_period,
)

from .services.registration import (
    create_registration,
    PlayerAlreadyClaimedError,
    PlayerNameUnavailableError,
)

from .services.player_game_results import build_player_history_with_summary
from .services.player_game_history_comparison import build_player_history_comparison


def game_history(request):
    filter_form = PlayerGameHistoryFilterForm(
        request.GET or None,
    )

    selected_player = None
    selected_secondary_player = None

    player_history = None
    player_history_summary = None
    secondary_history_summary = None

    comparison_rows = None

    is_comparison = False
    has_results = False

    if filter_form.is_valid():
        selected_player = filter_form.cleaned_data["player"]
        selected_secondary_player = filter_form.cleaned_data["secondary_player"]

        is_comparison = selected_secondary_player is not None

        start_date = filter_form.cleaned_data["start_date"]
        end_date = filter_form.cleaned_data["end_date"]

        action = request.GET.get("action", "custom")

        if action == "this_month":
            current_date = timezone.localdate()

            start_date = current_date.replace(day=1)
            end_date = current_date

        elif action == "all":
            start_date = None
            end_date = None

        if is_comparison:
            comparison = build_player_history_comparison(
                primary_player=selected_player,
                secondary_player=selected_secondary_player,
                start_date=start_date,
                end_date=end_date,
            )

            comparison_rows = comparison.rows
            player_history_summary = comparison.primary_summary
            secondary_history_summary = comparison.secondary_summary

            has_results = bool(comparison_rows)

        else:
            history = build_player_history_with_summary(
                player=selected_player,
                start_date=start_date,
                end_date=end_date,
            )

            player_history = history.daily_results
            player_history_summary = history.summary

            has_results = bool(player_history)

    context = {
        "filter_form": filter_form,
        "selected_player": selected_player,
        "selected_secondary_player": selected_secondary_player,
        "is_comparison": is_comparison,

        "player_history": player_history,
        "player_history_summary": player_history_summary,

        "comparison_rows": comparison_rows,
        "secondary_history_summary": secondary_history_summary,

        "has_results": has_results,
    }

    return render(
        request,
        "portal/game_history.html",
        context,
    )

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
    
class GameCreateView(LoginRequiredMixin, View):
    template_name = "portal/game_create.html"

    def get(self, request):
        acting_player = getattr(request.user, "player", None)
        if acting_player is None:
            raise PermissionDenied
        
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
        acting_player = getattr(request.user, "player", None)

        if acting_player is None:
            raise PermissionDenied
        
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
                acting_player=acting_player,
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

def game_detail(request, pk):
    # When retrieving this game I'm going to need its game results, and the player associated
    # with each result
    game = get_object_or_404(
        Game.objects.prefetch_related(
            "results__player",
        ),
        pk=pk,
    )
    
    context = {
        "game": game,
    }

    return render(
        request,
        "portal/game_detail.html",
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
    selected_period_label = None

    is_comparison = False

    monthly_scores = None
    secondary_monthly_scores = None
    monthly_comparisons = None
    monthly_chart_html = None

    score_distribution = None
    secondary_score_distribution = None
    score_distribution_comparison = None
    statistical_comparisons = None
    has_comparison_statistics = False
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

            if is_comparison and secondary_game_results.exists():
                secondary_score_distribution = calculate_score_distribution(
                    game_results=secondary_game_results,
                )

                score_distribution_comparison = calculate_score_distribution_comparison(
                    primary_game_results=game_results,
                    secondary_game_results=secondary_game_results,
                    primary_score_distribution=score_distribution,
                    secondary_score_distribution=secondary_score_distribution,
                )

                statistical_comparisons = compare_score_distributions(
                    primary_score_distribution=score_distribution,
                    secondary_score_distribution=secondary_score_distribution,
                )

                has_comparison_statistics = True

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

            if is_comparison and score_distribution_comparison is not None:
                distribution_figure = build_score_distribution_comparison_chart(
                    score_distribution_comparison=score_distribution_comparison,
                    primary_player=selected_player,
                    secondary_player=selected_secondary_player,
                )
            else:
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
        "secondary_score_distribution": secondary_score_distribution,
        "score_distribution_comparison": score_distribution_comparison,
        "statistical_comparisons": statistical_comparisons,
        "has_comparison_statistics": has_comparison_statistics,
        "distribution_chart_html": distribution_chart_html,

        "has_results": has_results,
    }

    return render(
        request,
        "portal/player_score_trends.html",
        context,
    )

@login_required
def account(request):
    player = getattr(request.user, "player", None)

    context = {
        "player": player,
    }

    return render(
        request,
        "portal/account.html",
        context,
    )

def register(request):
    if request.user.is_authenticated:
        return redirect("portal:account")

    if request.method == "POST":
        form = RegistrationForm(request.POST)

        if form.is_valid():
            try:
                create_registration(
                    first_name=form.cleaned_data["first_name"],
                    last_name=form.cleaned_data["last_name"],
                    username=form.cleaned_data["username"],
                    email=form.cleaned_data["email"],
                    password=form.cleaned_data["password1"],
                    existing_player=form.cleaned_data["existing_player"],
                    new_player_name=form.cleaned_data["new_player_name"],
                )
            except PlayerAlreadyClaimedError:
                form.add_error(
                    "existing_player",
                    "This player has already been linked to another account.",
                )
            except PlayerNameUnavailableError:
                form.add_error(
                    "new_player_name",
                    "This player name is no longer available.",
                )
            else:
                messages.success(
                    request,
                    "Your registration request was submitted and is awaiting approval.",
                )

                return redirect("login")

    else:
        form = RegistrationForm()

    context = {
        "form": form,
    }

    return render(
        request,
        "registration/registration.html",
        context,
    )