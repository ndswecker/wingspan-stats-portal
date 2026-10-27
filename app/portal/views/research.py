from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseBadRequest
from django.shortcuts import render
from django.views.decorators.http import require_GET

from ..forms import TurnOrderResearchFilterForm

from ..services.research.turn_order_analysis import (
    get_starting_position_analysis,
    get_direct_preceding_analysis,
    get_player_spacing_analysis,
)

from ..services.research.turn_order_charts import (
    build_starting_position_win_rate_chart,
    build_starting_position_score_chart,
    build_starting_position_score_differential_chart,
    build_starting_position_turn_order_chart,
    build_direct_preceding_win_rate_chart,
    build_direct_preceding_score_chart,
    build_direct_preceding_score_differential_chart,
    build_player_spacing_win_rate_chart,
    build_player_spacing_score_chart,
    build_player_spacing_score_differential_chart,
)

from ..services.research.turn_order_research import (
    build_turn_order_dataset,
)

@login_required
def research_home(request):
    """
    Staff-only landing page for Wingspan research.

    Provides navigation to available research studies.
    """

    # 1. Require staff privileges.
    if not request.user.is_staff:
        raise PermissionDenied

    # 2. Render the research landing page.
    return render(
        request,
        "portal/research/research.html",
    )


@login_required
def turn_order_research(request):
    """
    Staff-only page for turn-order research.

    Renders the research filters and hypothesis sections.
    Statistical analyses are executed independently through
    execute_turn_order_hypothesis().
    """

    # 1. Require staff privileges.
    if not request.user.is_staff:
        raise PermissionDenied

    # 2. Initialize the research filter form.
    filter_form = TurnOrderResearchFilterForm()

    # 3. Assemble the initial template context.
    context = {
        "filter_form": filter_form,
        "starting_position_analysis": None,
        "starting_position_charts": None,
        "direct_preceding_analysis": None,
        "direct_preceding_charts": None,
        "player_spacing_analysis": None,
        "player_spacing_charts": None,
    }

    # 4. Render the research page.
    return render(
        request,
        "portal/research/turn_order_research.html",
        context,
    )


@login_required
@require_GET
def execute_turn_order_hypothesis(request):
    """
    Execute a single turn-order research hypothesis.

    This endpoint will return an HTML fragment for HTMX.
    """

    # 1. Require staff privileges.
    if not request.user.is_staff:
        raise PermissionDenied

    # 2. Identify the requested hypothesis.
    hypothesis = request.GET.get("hypothesis")

    if hypothesis not in ("h1", "h2", "h3"):
        return HttpResponseBadRequest(
            "Invalid hypothesis. Expected h1, h2, or h3."
        )

    # 3. Validate the research filters.
    filter_form = TurnOrderResearchFilterForm(request.GET)

    if not filter_form.is_valid():
        return HttpResponseBadRequest(
            "Invalid research filters."
        )

    # 4. Extract the validated research parameters.
    principal_player = filter_form.cleaned_data["principal_player"]
    opponent_player = filter_form.cleaned_data["opponent_player"]
    start_date = filter_form.cleaned_data["start_date"]
    end_date = filter_form.cleaned_data["end_date"]

    # 5. Build the research dataset.
    dataset = build_turn_order_dataset(
        principal_player=principal_player,
        opponent_player=opponent_player,
        start_date=start_date,
        end_date=end_date,
    )

    if hypothesis == "h1":
        # Execute H1 statistical analysis.
        analysis = get_starting_position_analysis(
            dataset=dataset,
        )

        # Configure Plotly charts.
        chart_config = {
            "displayModeBar": False,
            "scrollZoom": False,
            "doubleClick": False,
            "displaylogo": False,
        }

        charts = None
        statistics = analysis.statistics

        if statistics.total_games > 0:
            # Generate the three H1 figures.
            win_rate_figure = build_starting_position_win_rate_chart(
                statistics=statistics,
                principal_player_name=str(dataset.principal_player),
                start_date=dataset.start_date,
                end_date=dataset.end_date,
            )

            score_figure = build_starting_position_score_chart(
                statistics=statistics,
                principal_player_name=str(dataset.principal_player),
                start_date=dataset.start_date,
                end_date=dataset.end_date,
            )

            differential_figure = build_starting_position_score_differential_chart(
                statistics=statistics,
                principal_player_name=str(dataset.principal_player),
                start_date=dataset.start_date,
                end_date=dataset.end_date,
            )

            turn_order_figure = build_starting_position_turn_order_chart(
                statistics=analysis.turn_order_statistics,
                principal_player_name=dataset.principal_player.name,
                opponent_player_name=dataset.opponent_player.name,
                start_date=dataset.start_date,
                end_date=dataset.end_date,
            )

            # Convert figures to HTML.
            charts = {
                "win_rate": win_rate_figure.to_html(
                    full_html=False,
                    include_plotlyjs=False,
                    config=chart_config,
                ),
                "score": score_figure.to_html(
                    full_html=False,
                    include_plotlyjs=False,
                    config=chart_config,
                ),
                "score_differential": differential_figure.to_html(
                    full_html=False,
                    include_plotlyjs=False,
                    config=chart_config,
                ),
                "turn_order": turn_order_figure.to_html(
                    full_html=False,
                    include_plotlyjs=False,
                    config=chart_config,
                )
            }

        # Render the existing H1 results partial.
        return render(
            request,
            "portal/research/partials/turn_order/_starting_position.html",
            {
                "starting_position_analysis": analysis,
                "starting_position_charts": charts,
            },
        )

    # 7. Execute H2: Direct Preceding.
    if hypothesis == "h2":
        analysis = get_direct_preceding_analysis(
            dataset=dataset,
        )

        charts = None
        statistics = analysis.statistics

        chart_config = {
            "displayModeBar": False,
            "scrollZoom": False,
            "doubleClick": False,
            "displaylogo": False,
        }

        if statistics.total_games > 0:
            win_rate_figure = build_direct_preceding_win_rate_chart(
                statistics=statistics,
                principal_player_name=str(dataset.principal_player),
                start_date=dataset.start_date,
                end_date=dataset.end_date,
            )

            score_figure = build_direct_preceding_score_chart(
                statistics=statistics,
                principal_player_name=str(dataset.principal_player),
                start_date=dataset.start_date,
                end_date=dataset.end_date,
            )

            differential_figure = build_direct_preceding_score_differential_chart(
                statistics=statistics,
                principal_player_name=str(dataset.principal_player),
                start_date=dataset.start_date,
                end_date=dataset.end_date,
            )

            charts = {
                "win_rate": win_rate_figure.to_html(
                    full_html=False,
                    include_plotlyjs=False,
                    config=chart_config,
                ),
                "score": score_figure.to_html(
                    full_html=False,
                    include_plotlyjs=False,
                    config=chart_config,
                ),
                "score_differential": differential_figure.to_html(
                    full_html=False,
                    include_plotlyjs=False,
                    config=chart_config,
                ),
            }

        return render(
            request,
            "portal/research/partials/turn_order/_direct_preceding.html",
            {
                "direct_preceding_analysis": analysis,
                "direct_preceding_charts": charts,
            },
        )

    # 8. Execute H3: Player Spacing.
    if hypothesis == "h3":
        analysis = get_player_spacing_analysis(
            dataset=dataset,
        )

        charts = None
        statistics = analysis.statistics

        chart_config = {
            "displayModeBar": False,
            "scrollZoom": False,
            "doubleClick": False,
            "displaylogo": False,
        }

        if statistics.total_games > 0:
            win_rate_figure = build_player_spacing_win_rate_chart(
                statistics=statistics,
                principal_player_name=str(dataset.principal_player),
                start_date=dataset.start_date,
                end_date=dataset.end_date,
            )

            score_figure = build_player_spacing_score_chart(
                statistics=statistics,
                principal_player_name=str(dataset.principal_player),
                start_date=dataset.start_date,
                end_date=dataset.end_date,
            )

            differential_figure = (
                build_player_spacing_score_differential_chart(
                    statistics=statistics,
                    principal_player_name=str(dataset.principal_player),
                    start_date=dataset.start_date,
                    end_date=dataset.end_date,
                )
            )

            charts = {
                "win_rate": win_rate_figure.to_html(
                    full_html=False,
                    include_plotlyjs=False,
                    config=chart_config,
                ),
                "score": score_figure.to_html(
                    full_html=False,
                    include_plotlyjs=False,
                    config=chart_config,
                ),
                "score_differential": differential_figure.to_html(
                    full_html=False,
                    include_plotlyjs=False,
                    config=chart_config,
                ),
            }

        return render(
            request,
            "portal/research/partials/turn_order/_player_spacing.html",
            {
                "player_spacing_analysis": analysis,
                "player_spacing_charts": charts,
            },
        )
