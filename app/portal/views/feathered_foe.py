from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from ..forms import FeatheredFoeForm
from ..services.feathered_foe import build_feathered_foe

@login_required
def feathered_foe(request):
    acting_player = request.user.player

    filter_form = FeatheredFoeForm(
        request.GET or None,
        acting_player=acting_player,
    )

    feathered_foe_result = None

    if filter_form.is_valid():
        primary_player = filter_form.cleaned_data["primary_player"]
        secondary_player = filter_form.cleaned_data["secondary_player"]
        start_date = filter_form.cleaned_data["start_date"]
        end_date = filter_form.cleaned_data["end_date"]
        winner_method = filter_form.cleaned_data["winner_method"]

        feathered_foe_result = build_feathered_foe(
            primary_player=primary_player,
            secondary_player=secondary_player,
            start_date=start_date,
            end_date=end_date,
            fully_confirmed_only=True,
            winner_method=winner_method,
        )

    context = {
        "filter_form": filter_form,
        "feathered_foe": feathered_foe_result,
    }

    return render(
        request,
        "portal/feathered_foe.html",
        context,
    )