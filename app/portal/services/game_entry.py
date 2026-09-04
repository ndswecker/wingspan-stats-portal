from django.db import transaction

from ..models import Game, GameResult, Player

@transaction.atomic
def create_game(
    *,
    game_data, 
    result_forms,
    acting_player: Player,
):
    game = Game.objects.create(
        date_played=game_data["date_played"],
        human_player_mode=game_data["human_player_mode"],
    )

    for form in result_forms:
        result_data = form.cleaned_data

        if not result_data.get("is_populated"):
            continue

        result_player = result_data["player"]
        is_confirmed = False
        if result_player == acting_player:
            is_confirmed = True

        GameResult.objects.create(
            game=game,
            player=result_data["player"],
            score=result_data["score"],
            turn_order=result_data["turn_order"],
            is_confirmed=is_confirmed
        )

    return game

@transaction.atomic
def update_game(
    *,
    game: Game,
    game_data: dict,
    result_forms,
    acting_player: Player | None,
):
    """
    Update an existing game and its associated results.

    The caller is responsible for validating the GameForm and
    GameResultEditFormSet before calling this service.

    Confirmation state is determined by who performed each result change.
    """

    # Snapshot the existing GameResult records before making any changes.
    #
    # A validated ModelForm may already have applied submitted values to
    # form.instance, so the database records are our reliable source for
    # determining what actually changed.
    existing_results = {
        result.pk: result
        for result in GameResult.objects.select_for_update().filter(
            game=game,
        )
    }

    # Update the Game itself.
    game.date_played = game_data["date_played"]
    game.human_player_mode = game_data["human_player_mode"]

    game.save(
        update_fields=[
            "date_played",
            "human_player_mode",
        ]
    )

    forms_to_create = []
    forms_to_update = []

    # First determine which existing results must be deleted,
    # which results are being reassigned to another player,
    # and which rows are ordinary updates.
    for form in result_forms:
        delete_requested = form.cleaned_data.get(
            "DELETE",
            False,
        )

        existing_result_id = form.instance.pk

        # This is an existing GameResult.
        if existing_result_id:
            original_result = existing_results[
                existing_result_id
            ]

            if delete_requested:
                original_result.delete()
                continue

            submitted_player = form.cleaned_data["player"]

            player_changed = (
                submitted_player.pk
                != original_result.player_id
            )

            if player_changed:
                # Changing the player assignment is treated as removing
                # the old GameResult and creating a new GameResult for
                # the newly selected player.
                original_result.delete()
                forms_to_create.append(form)
                continue

            forms_to_update.append(form)
            continue

        # This is one of the extra ModelForm rows.
        if delete_requested:
            continue

        # Completely unused extra rows should not create GameResults.
        if not form.has_changed():
            continue

        forms_to_create.append(form)

    # Temporarily clear turn order for surviving existing results.
    #
    # This prevents transient uniqueness violations when two players swap
    # turn orders. For example, changing 1 -> 2 and 2 -> 1 cannot safely
    # be performed one row at a time while both old values still exist.
    GameResult.objects.filter(
        game=game,
    ).update(
        turn_order=None,
    )

    # Update existing GameResults whose player assignment did not change.
    for form in forms_to_update:
        original_result = existing_results[
            form.instance.pk
        ]

        result_data = form.cleaned_data

        submitted_score = result_data["score"]
        submitted_turn_order = result_data["turn_order"]

        score_changed = (
            submitted_score
            != original_result.score
        )

        acting_player_owns_result = False

        if acting_player is not None:
            if acting_player.pk == original_result.player_id:
                acting_player_owns_result = True

        is_confirmed = original_result.is_confirmed

        if score_changed:
            # An owner changing their own score confirms it.
            # Anyone else changing the score invalidates confirmation.
            if acting_player_owns_result:
                is_confirmed = True
            else:
                is_confirmed = False

        else:
            # Later, when confirm_score is added to the edit form,
            # an owner may explicitly confirm an unchanged score.
            confirm_score = result_data.get(
                "confirm_score",
                False,
            )

            if (
                acting_player_owns_result
                and confirm_score
            ):
                is_confirmed = True

        original_result.score = submitted_score
        original_result.turn_order = submitted_turn_order
        original_result.is_confirmed = is_confirmed

        original_result.save(
            update_fields=[
                "score",
                "turn_order",
                "is_confirmed",
            ]
        )

    # Create genuinely new results as well as player reassignments.
    #
    # A reassignment is deliberately treated as:
    #
    # old result deleted
    # +
    # new result created
    #
    # Therefore the new owner starts unconfirmed unless they are the
    # player currently performing the edit.
    for form in forms_to_create:
        result_data = form.cleaned_data

        result_player = result_data["player"]

        is_confirmed = False

        if acting_player is not None:
            if acting_player.pk == result_player.pk:
                is_confirmed = True

        GameResult.objects.create(
            game=game,
            player=result_player,
            score=result_data["score"],
            turn_order=result_data["turn_order"],
            is_confirmed=is_confirmed,
        )