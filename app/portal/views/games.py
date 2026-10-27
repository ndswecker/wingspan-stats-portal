from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.decorators.http import require_POST

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

def game_detail(request, pk):
    # When retrieving this game I'm going to need its game results, and the player associated
    # with each result
    game = get_object_or_404(
        Game.objects.prefetch_related(
            "results__player",
        ),
        pk=pk,
    )

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