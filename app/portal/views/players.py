from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone

from ..models import Game

from ..forms import (
    PlayerGameHistoryFilterForm,
    PlayerStatisticsFilterForm,
    PlayerScoreTrendsFilterForm,
)

from ..services.player_game_results import (
    build_player_history_with_summary,
)

from ..services.player_game_history_comparison import (
    build_player_history_comparison,
)

from ..services.game_result_selection import select_game_results
from ..services.player_general_stats import calculate_general_stats

from ..services.player_score_trends import (
    calculate_monthly_score_averages,
    compare_monthly_score_averages,
    resolve_score_trend_date_range,
)

from ..services.player_score_trend_chart import (
    build_monthly_score_chart,
    build_monthly_score_comparison_chart,
)

from ..services.player_score_distribution import (
    calculate_score_distribution,
    calculate_score_distribution_comparison,
    compare_score_distributions,
)

from ..services.player_score_distribution_chart import (
    build_score_distribution_chart,
    build_score_distribution_comparison_chart,
)

from ..services.player_game_scatter_chart import (
    build_game_scatter_chart,
)

from ..services.player_game_score_gap import (
    build_game_score_gaps,
    calculate_victory_margin_analysis,
)

from ..services.player_game_score_gap_chart import (
    build_game_score_gap_chart,
)

@login_required
def competitive_history(request):
    acting_player = request.user.player

    filter_form = PlayerGameHistoryFilterForm(
        request.GET or None,
        acting_player=acting_player,
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
                fully_confirmed_only=True,
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
                fully_confirmed_only=True,
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
        "portal/competitive_history.html",
        context,
    )

@login_required
def player_overview(request):
    acting_player = request.user.player

    form_data = request.GET.copy() if request.GET else None

    if form_data is not None:
        action = form_data.get("action")

        if action == "this_month":
            today = timezone.localdate()
            form_data["start_date"] = today.replace(day=1).isoformat()
            form_data["end_date"] = today.isoformat()

        elif action == "all":
            form_data["start_date"] = ""
            form_data["end_date"] = ""

    filter_form = PlayerStatisticsFilterForm(
        form_data,
        acting_player=acting_player,
    )

    general_stats = None
    game_results = None
    selected_player = None
    selected_game_type_label = None
    selected_start_date = None
    selected_end_date = None

    if filter_form.is_valid():
        selected_player = filter_form.cleaned_data["player"]
        game_type = Game.HumanPlayerMode(
            filter_form.cleaned_data["game_type"]
        )
        selected_game_type_label = game_type.label

        selected_start_date = filter_form.cleaned_data["start_date"]
        selected_end_date = filter_form.cleaned_data["end_date"]

        game_results = select_game_results(
            player=selected_player,
            game_type=game_type,
            start_date=selected_start_date,
            end_date=selected_end_date,
        )

        general_stats = calculate_general_stats(
            game_results=game_results,
        )

    context = {
        "filter_form": filter_form,
        "general_stats": general_stats,
        "game_results": game_results,
        "selected_player": selected_player,
        "selected_game_type_label": selected_game_type_label,
        "selected_start_date": selected_start_date,
        "selected_end_date": selected_end_date,
    }

    return render(
        request,
        "portal/player_overview.html",
        context,
    )

@login_required
def player_score_trends(request):
    acting_player = request.user.player

    form_data = request.GET.copy() if request.GET else None

    if form_data is not None:
        action = form_data.get("action")

        if action == "this_month":
            today = timezone.localdate()
            form_data["start_date"] = today.replace(day=1).isoformat()
            form_data["end_date"] = today.isoformat()

        elif action == "all":
            form_data["start_date"] = ""
            form_data["end_date"] = ""

    filter_form = PlayerScoreTrendsFilterForm(
        form_data,
        acting_player=acting_player,
    )

    selected_player = None
    selected_secondary_player = None

    selected_game_type_label = None

    selected_start_date = None
    selected_end_date = None

    is_comparison = False

    monthly_scores = None
    secondary_monthly_scores = None
    monthly_comparisons = None
    monthly_chart_html = None
    game_scatter_chart_html = None

    score_distribution = None
    secondary_score_distribution = None
    score_distribution_comparison = None
    statistical_comparisons = None
    has_comparison_statistics = False
    distribution_chart_html = None

    game_score_gaps = None
    game_score_gap_chart = None
    game_score_gap_chart_html = None
    game_score_gap_figure = None
    show_game_score_gap = False

    victory_margin_analysis = None

    has_results = False

    if filter_form.is_valid():
        selected_player = filter_form.cleaned_data["player"]
        selected_secondary_player = filter_form.cleaned_data["secondary_player"]
        is_comparison = selected_secondary_player is not None

        game_type = Game.HumanPlayerMode(
            filter_form.cleaned_data["game_type"],
        )
        selected_game_type_label = game_type.label

        selected_start_date = filter_form.cleaned_data["start_date"]
        selected_end_date = filter_form.cleaned_data["end_date"]

        game_results = select_game_results(
            player=selected_player,
            game_type=game_type,
            start_date=selected_start_date,
            end_date=selected_end_date,
            fully_confirmed_only=True,
        )

        secondary_game_results = None

        if is_comparison:
            secondary_game_results = select_game_results(
                player=selected_secondary_player,
                game_type=game_type,
                start_date=selected_start_date,
                end_date=selected_end_date,
                fully_confirmed_only=True,
            )

            if game_type == Game.HumanPlayerMode.MULTIPLE:
                show_game_score_gap = True

                game_score_gaps = build_game_score_gaps(
                    primary_player=selected_player,
                    secondary_player=selected_secondary_player,
                    start_date=selected_start_date,
                    end_date=selected_end_date,
                    fully_confirmed_only=True,
                )

                if game_score_gaps:
                    game_score_gap_figure = build_game_score_gap_chart(
                        score_gaps=game_score_gaps,
                        primary_player=selected_player,
                        secondary_player=selected_secondary_player,
                    )

                    victory_margin_analysis = calculate_victory_margin_analysis(
                        primary_player=selected_player,
                        secondary_player=selected_secondary_player,
                        score_gaps=game_score_gaps,
                    )

        has_results = game_results.exists()

        if has_results:

            score_trend_date_range = resolve_score_trend_date_range(
                primary_game_results=game_results,
                secondary_game_results=secondary_game_results,
                start_date=selected_start_date,
                end_date=selected_end_date,
            )

            monthly_scores = calculate_monthly_score_averages(
                game_results=game_results,
                start_date=score_trend_date_range.start_date,
                end_date=score_trend_date_range.end_date,
            )

            if is_comparison:
                secondary_monthly_scores = calculate_monthly_score_averages(
                    game_results=secondary_game_results,
                    start_date=score_trend_date_range.start_date,
                    end_date=score_trend_date_range.end_date,
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
                )
            else:
                monthly_figure = build_monthly_score_chart(
                    monthly_scores=monthly_scores,
                    player=selected_player,
                    game_type_label=selected_game_type_label,
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

            game_scatter_figure = build_game_scatter_chart(
                primary_game_results=game_results,
                secondary_game_results=secondary_game_results,
                primary_player=selected_player,
                secondary_player=selected_secondary_player,
                start_date=score_trend_date_range.start_date,
                end_date=score_trend_date_range.end_date,
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

            game_scatter_chart_html = game_scatter_figure.to_html(
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

            if game_score_gap_figure is not None:
                game_score_gap_chart_html = game_score_gap_figure.to_html(
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

        "monthly_scores": monthly_scores,
        "secondary_monthly_scores": secondary_monthly_scores,
        "monthly_comparisons": monthly_comparisons,
        "monthly_chart_html": monthly_chart_html,

        "game_scatter_chart_html": game_scatter_chart_html,

        "score_distribution": score_distribution,
        "secondary_score_distribution": secondary_score_distribution,
        "score_distribution_comparison": score_distribution_comparison,
        "statistical_comparisons": statistical_comparisons,
        "has_comparison_statistics": has_comparison_statistics,
        "distribution_chart_html": distribution_chart_html,

        "game_score_gaps": game_score_gaps,
        "game_score_gap_chart_html": game_score_gap_chart_html,
        "show_game_score_gap": show_game_score_gap,
        "victory_margin_analysis": victory_margin_analysis,

        "has_results": has_results,
    }

    return render(
        request,
        "portal/player_score_trends.html",
        context,
    )
