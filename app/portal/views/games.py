from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.decorators.http import require_POST
from django.http import HttpResponseBadRequest

from ..models import Game, GameResult

from ..forms import (
    GameForm,
    GameResultFormSet,
    GameResultEditFormSet,
)

from ..services.game_entry import (
    create_game,
    update_game,
)

from ..services.player_access import (
    can_view_game,
)

from ..services.player_game_results import confirm_game_result

from ..permissions import can_manage_game

class GameCreateView(LoginRequiredMixin, View):
    template_name = "portal/game_create.html"

    def get(self, request):
        acting_player = getattr(request.user, "player", None)
        if acting_player is None:
            raise PermissionDenied
        
        game_form = GameForm()

        result_formset = GameResultFormSet(
            prefix="results",
            acting_player=acting_player,
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
            acting_player=acting_player,
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


@login_required
@require_POST
def game_result_rows(request):
    """
    Add or remove player-result rows during game creation.

    Reconstruct the submitted formset and return updated HTML.
    No Game or GameResult records are created.
    """

    acting_player = getattr(
        request.user,
        "player",
        None,
    )

    if acting_player is None:
        raise PermissionDenied

    action = request.POST.get("action")

    if action not in ("add", "remove"):
        return HttpResponseBadRequest(
            "Invalid player-row action."
        )

    # Retrieve and validate the formset management data.
    result_formset = GameResultFormSet(
        request.POST,
        prefix="results",
        acting_player=acting_player,
    )

    if not result_formset.management_form.is_valid():
        return HttpResponseBadRequest(
            "Invalid formset management data."
        )

    total_forms = result_formset.total_form_count()

    # This endpoint only manages new game results.
    if (
        total_forms < 1
        or total_forms > 5
        or result_formset.initial_form_count() != 0
    ):
        return HttpResponseBadRequest(
            "Invalid number of player rows."
        )

    # Make a mutable copy of the submitted data.
    form_data = request.POST.copy()

    if action == "add":
        if total_forms >= 5:
            return HttpResponseBadRequest(
                "A maximum of five players is allowed."
            )

        form_data["results-TOTAL_FORMS"] = str(
            total_forms + 1
        )

    elif action == "remove":
        if total_forms <= 1:
            return HttpResponseBadRequest(
                "At least one player row is required."
            )

        try:
            remove_index = int(
                request.POST.get("row_index", "")
            )
        except (TypeError, ValueError):
            return HttpResponseBadRequest(
                "Invalid player row."
            )

        if not 0 <= remove_index < total_forms:
            return HttpResponseBadRequest(
                "Invalid player row."
            )

        # Shift subsequent rows upward to maintain
        # consecutive Django formset indexes.
        fields = (
            "player",
            "score",
            "turn_order",
            "DELETE",
        )

        for index in range(
            remove_index,
            total_forms - 1,
        ):
            for field in fields:
                source = (
                    f"results-{index + 1}-{field}"
                )
                destination = (
                    f"results-{index}-{field}"
                )

                if source in request.POST:
                    form_data[destination] = (
                        request.POST[source]
                    )
                else:
                    form_data.pop(destination, None)

        # Remove the now-unused final row.
        last_index = total_forms - 1

        for field in fields:
            form_data.pop(
                f"results-{last_index}-{field}",
                None,
            )

        form_data["results-TOTAL_FORMS"] = str(
            total_forms - 1
        )

    # Rebuild the formset using the updated data.
    result_formset = GameResultFormSet(
        form_data,
        prefix="results",
        acting_player=acting_player,
    )

    return render(
        request,
        "portal/game_result_rows.html",
        {
            "result_formset": result_formset,
        },
    )



@login_required
@require_POST
def game_edit_result_rows(request, pk):
    """
    Add or remove player-result rows while editing a game.

    Existing results retain their database identities.
    Changes are not persisted until Save Changes.
    """

    game = get_object_or_404(
        Game,
        pk=pk,
    )

    if not can_manage_game(request.user, game):
        raise PermissionDenied

    acting_player = getattr(
        request.user,
        "player",
        None,
    )

    if acting_player is None:
        raise PermissionDenied

    action = request.POST.get("action")

    if action not in ("add", "remove"):
        return HttpResponseBadRequest(
            "Invalid player-row action."
        )

    form_data = request.POST.copy()

    existing_results = game.results.all()

    result_formset = GameResultEditFormSet(
        form_data,
        queryset=existing_results,
        prefix="results",
        human_player_mode=game.human_player_mode,
        acting_player=acting_player,
    )

    if not result_formset.management_form.is_valid():
        return HttpResponseBadRequest(
            "Invalid formset management data."
        )

    total_forms = result_formset.total_form_count()
    initial_forms = result_formset.initial_form_count()

    # Existing GameResult records must retain their
    # original formset positions and identities.
    if initial_forms != existing_results.count():
        return HttpResponseBadRequest(
            "Invalid initial form count."
        )

    if total_forms < initial_forms or total_forms > 25:
        return HttpResponseBadRequest(
            "Invalid number of result forms."
        )

    # Count only rows that have not been marked for deletion.
    active_indices = [
        index
        for index in range(total_forms)
        if form_data.get(
            f"results-{index}-DELETE"
        ) not in ("on", "true", "True", "1")
    ]

    if action == "add":
        if len(active_indices) >= 5:
            return HttpResponseBadRequest(
                "A maximum of five players is allowed."
            )

        form_data["results-TOTAL_FORMS"] = str(
            total_forms + 1
        )

    elif action == "remove":
        try:
            remove_index = int(
                request.POST.get("row_index", "")
            )
        except (TypeError, ValueError):
            return HttpResponseBadRequest(
                "Invalid player row."
            )

        if remove_index not in active_indices:
            return HttpResponseBadRequest(
                "Invalid player row."
            )

        if len(active_indices) <= 1:
            return HttpResponseBadRequest(
                "At least one player is required."
            )

        # Mark the selected form for deletion.
        # Do not reindex existing ModelFormSet rows.
        form_data[
            f"results-{remove_index}-DELETE"
        ] = "on"

    result_formset = GameResultEditFormSet(
        form_data,
        queryset=existing_results,
        prefix="results",
        human_player_mode=game.human_player_mode,
        acting_player=acting_player,
    )

    return render(
        request,
        "portal/game_edit_result_rows.html",
        {
            "game": game,
            "result_formset": result_formset,
            "active_form_count": count_active_result_forms(
                result_formset
            ),
        },
    )



@login_required
def game_detail(request, pk):
    # When retrieving this game I'm going to need its game results, and the player associated
    # with each result
    game = get_object_or_404(
        Game.objects.prefetch_related(
            "results__player",
        ),
        pk=pk,
    )

    if not can_view_game(
        user=request.user,
        game=game,
    ):
        raise PermissionDenied

    user_can_manage_game = can_manage_game(
        request.user,
        game,
    )

    context = {
        "game": game,
        "user_can_manage_game": user_can_manage_game,
    }

    return render(
        request,
        "portal/game_detail.html",
        context,
    )


def count_active_result_forms(result_formset):
    """
    Count result forms that have not been marked for deletion.

    Includes existing and newly added results.
    Does not modify or validate the formset.
    """

    return sum(
        1
        for form in result_formset.forms
        if not form["DELETE"].value()
    )

@login_required
def game_edit(request, pk):
    game = get_object_or_404(
        Game.objects.prefetch_related(
            "results__player",
        ),
        pk=pk,
    )

    if not can_manage_game(
        request.user,
        game,
    ):
        raise PermissionDenied

    acting_player = request.user.player

    if request.method == "POST":
        game_form = GameForm(
            request.POST,
            instance=game,
        )

        game_form_is_valid = game_form.is_valid()

        human_player_mode = request.POST.get(
            "human_player_mode"
        )

        if game_form_is_valid:
            human_player_mode = (
                game_form.cleaned_data["human_player_mode"]
            )

        result_formset = GameResultEditFormSet(
            request.POST,
            queryset=game.results.all(),
            prefix="results",
            human_player_mode=human_player_mode,
            acting_player=acting_player,
        )

        result_formset_is_valid = result_formset.is_valid()

        if (
            game_form_is_valid
            and result_formset_is_valid
        ):
            update_game(
                game=game,
                game_data=game_form.cleaned_data,
                result_forms=result_formset.forms,
                acting_player=acting_player,
            )

            return redirect(
                "portal:game-detail",
                pk=game.pk,
            )

    else:
        # Populate the Game form with the existing Game record.
        game_form = GameForm(
            instance=game,
        )

        # Populate the result formset with all existing GameResult records
        # belonging to this game.
        # The ModelFormSet will also provide extra blank forms so that
        # another result can be added to the existing game.
        result_formset = GameResultEditFormSet(
            queryset=game.results.all(),
            prefix="results",
            human_player_mode=game.human_player_mode,
            acting_player=acting_player,
        )

    context = {
        "game": game,
        "game_form": game_form,
        "result_formset": result_formset,
        "active_form_count": count_active_result_forms(result_formset),
    }

    return render(
        request,
        "portal/game_edit.html",
        context,
    )


@login_required
@require_POST
def confirm_game_result_view(request, result_id):
    game_result = get_object_or_404(
        GameResult,
        pk=result_id,
    )

    acting_player = getattr(
        request.user,
        "player",
        None,
    )

    if acting_player is None:
        raise PermissionDenied

    confirm_game_result(
        game_result=game_result,
        acting_player=acting_player,
    )

    return redirect(
        "portal:game-detail",
        pk=game_result.game_id,
    )