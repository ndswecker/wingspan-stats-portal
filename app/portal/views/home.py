from datetime import timedelta

from django.shortcuts import render
from django.utils import timezone

from ..forms import HomeLeaderboardFilterForm

from ..services.dashboard import (
    get_total_games_played,
    get_community_leaderboard,
    get_friends_leaderboard,
)


def home(request):
    """
    Render the Home page with Community and Friends leaderboards.

    Community:
        - Available to all visitors.
        - Includes only active Public players.
        - Displays the Top 10.

    Friends:
        - Available to authenticated users with a linked Player.
        - Includes the acting player and their active friends.

    Both leaderboards share the same filtering selections.
    """

    # ---------------------------------------------------------
    # 1. Initialize and validate the leaderboard filter form.
    # ---------------------------------------------------------

    # Bind the form to GET parameters when provided.
    # Otherwise, use an unbound form with default selections.
    if request.GET:
        filter_form = HomeLeaderboardFilterForm(
            request.GET,
        )
    else:
        filter_form = HomeLeaderboardFilterForm()

    # Use the submitted selections when valid.
    if filter_form.is_bound and filter_form.is_valid():

        selected_period = filter_form.cleaned_data["period"]
        selected_ranking_metric = filter_form.cleaned_data["ranking_metric"]
        selected_game_type = filter_form.cleaned_data["game_type"]

    else:
        # Default selections for initial load or invalid submissions.
        selected_period = "30"
        selected_ranking_metric = "average_score"
        selected_game_type = "all"

        # Replace an invalid bound form so the controls display
        # the same defaults used to generate the leaderboards.
        if filter_form.is_bound:
            filter_form = HomeLeaderboardFilterForm()

    # The dashboard service interprets None as all game types.
    if selected_game_type == "all":
        selected_game_type = None

    # ---------------------------------------------------------
    # 2. Calculate the selected date boundaries.
    # ---------------------------------------------------------

    today = timezone.localdate()

    # All time periods end today, excluding future-dated games.
    end_date = today

    if selected_period == "30":
        start_date = today - timedelta(
            days=29,
        )

    elif selected_period == "90":
        start_date = today - timedelta(
            days=89,
        )

    else:
        # All Time applies no lower date boundary.
        start_date = None

    # ---------------------------------------------------------
    # 3. Retrieve the site-wide game count.
    # ---------------------------------------------------------

    total_games_played = get_total_games_played()

    # ---------------------------------------------------------
    # 4. Build the Community leaderboard.
    # ---------------------------------------------------------

    # The Community leaderboard is identical for all visitors.
    community_leaderboard = get_community_leaderboard(
        start_date=start_date,
        end_date=end_date,
        ranking_metric=selected_ranking_metric,
        game_type=selected_game_type,
    )

    # ---------------------------------------------------------
    # 5. Build the Friends leaderboard when applicable.
    # ---------------------------------------------------------

    friends_leaderboard = []
    show_friends_leaderboard = False
    acting_player = None

    # Only authenticated users with a linked Player
    # receive a Friends leaderboard.
    if request.user.is_authenticated:

        acting_player = getattr(
            request.user,
            "player",
            None,
        )

        if acting_player is not None:

            show_friends_leaderboard = True

            friends_leaderboard = get_friends_leaderboard(
                user=request.user,
                start_date=start_date,
                end_date=end_date,
                ranking_metric=selected_ranking_metric,
                game_type=selected_game_type,
            )

    # ---------------------------------------------------------
    # 6. Prepare the template context.
    # ---------------------------------------------------------

    context = {
        "filter_form": filter_form,
        "total_games_played": total_games_played,
        "community_leaderboard": community_leaderboard,
        "friends_leaderboard": friends_leaderboard,
        "show_friends_leaderboard": show_friends_leaderboard,
        "acting_player": acting_player,
        "selected_period": selected_period,
        "selected_ranking_metric": selected_ranking_metric,
        "selected_game_type": selected_game_type,
        "start_date": start_date,
        "end_date": end_date,
    }

    return render(
        request,
        "portal/home.html",
        context,
    )