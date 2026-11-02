from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render

from ..forms import (
    RegistrationForm,
    PlayerPrivacyForm,
)

from ..services.player_game_results import (
    select_pending_game_results,
)

from ..services.registration import (
    create_registration,
    PlayerAlreadyClaimedError,
    PlayerNameUnavailableError,
    PlayerHandleUnavailableError,
)

@login_required
def account(request):
    player = getattr(
        request.user, 
        "player", 
        None,
    )

    pending_game_results = []
    privacy_form = None

    if request.method == "POST":
        if player is None:
            raise PermissionDenied

        privacy_form = PlayerPrivacyForm(
            request.POST,
            instance=player
        )

        if privacy_form.is_valid():
            privacy_form.save()

            messages.success(
                request,
                "Your privacy settings have been updated.",
            )

            return redirect("portal:account")

    if player is not None:
        pending_game_results = select_pending_game_results(
            player=player,
        )

        if privacy_form is None:
            privacy_form = PlayerPrivacyForm(
                instance=player,
            )

    context = {
        "player": player,
        "pending_game_results": pending_game_results,
        "privacy_form": privacy_form,
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
                    new_player_handle=form.cleaned_data["new_player_handle"],
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
            except PlayerHandleUnavailableError:
                form.add_error(
                    "new_player_handle",
                    "This player handle is no longer available.",
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
