from dataclasses import dataclass
from datetime import date
from enum import StrEnum

from django.db.models import Q, Count, Prefetch

from ..models import Player, Game, GameResult


class GamePrincipalOutcome(StrEnum):
    WIN = "win"
    LOSS = "loss"
    TIE = "tie"


@dataclass(frozen=True)
class TurnOrderGameRecord:
    """
    One qualifying game prepared for turn-order research.
    
    All player related values are expressed from the perspective of the
    principal player.
    """

    game_id: int
    date_played: date

    principal_player: Player
    opponent_player: Player

    principal_score: int
    opponent_score: int

    principal_turn_order: int
    opponent_turn_order: int

    winner: Player | None
    outcome: GamePrincipalOutcome
    score_differential: int

    npcs_after_principal: int
    npcs_before_principal: int
    principal_directly_precedes_opponent: bool


@dataclass(frozen=True)
class TurnOrderDataset:
    """
    A collection of qualifying games prepared for turn-order research.
    """

    principal_player: Player
    opponent_player: Player

    start_date: date | None
    end_date: date | None

    games: list[TurnOrderGameRecord]


def select_turn_order_games(
    *,
    principal_player: Player,
    opponent_player: Player,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[Game]:
    """
    Select competitive games containing only the principal player
    and opponent as recorded human participants.

    Both players must have recorded turn orders.
    Optional date boundaries are inclusive.

    Game results and associated players are prefetched for
    downstream processing.
    """
    if principal_player.pk == opponent_player.pk:
        raise ValueError("Principal player and opponent must be distinct.")

    required_player_count = 2
    selected_players = [principal_player, opponent_player]

    # 1. Select competitive games.
    games = Game.objects.filter(
        human_player_mode=Game.HumanPlayerMode.MULTIPLE,
    )

    # 2. Require exactly two recorded human players.
    games = games.annotate(
        player_count=Count("results"),
    ).filter(
        player_count=required_player_count,
    )

    # 3. Require both selected players to have recorded turn orders.
    eligible_player_result = Q(
        results__player__in=selected_players,
        results__turn_order__isnull=False,
    )

    games = games.annotate(
        eligible_player_count=Count(
            "results",
            filter=eligible_player_result,
        ),
    ).filter(
        eligible_player_count=required_player_count,
    )

    # 4. Apply optional date boundaries.
    if start_date is not None:
        games = games.filter(date_played__gte=start_date)

    if end_date is not None:
        games = games.filter(date_played__lte=end_date)

    # 5. Prefetch results and associated players.
    games = games.prefetch_related(
        Prefetch(
            "results",
            queryset=GameResult.objects.select_related("player"),
            to_attr="prefetched_results",
        )
    )

    # 6. Order and evaluate the queryset.
    games = games.order_by(
        "date_played",
        "id",
    )

    games = list(games)

    return games

def build_turn_order_game_record(
    *,
    game: Game,
    principal_player: Player,
    opponent_player: Player,
) -> TurnOrderGameRecord:
    """
    Transform one qualifying Game into a TurnOrderGameRecord.

    The game must have been retrieved through select_turn_order_games()
    and contain the prefetched_results attribute.

    All calculations are from the principal player's perspective.
    No database queries are performed.
    """

    # 1. Retrieve the results associated with this game.
    game_results = game.prefetched_results

    # 2. Identify the principal and opponent results.
    principal_result = None
    opponent_result = None

    for game_result in game_results:
        if game_result.player_id == principal_player.pk:
            principal_result = game_result

        elif game_result.player_id == opponent_player.pk:
            opponent_result = game_result

    # 3. Extract the scores and starting positions.
    principal_score = principal_result.score
    opponent_score = opponent_result.score

    principal_turn_order = principal_result.turn_order
    opponent_turn_order = opponent_result.turn_order

    # 4. Calculate the principal player's score differential.
    score_differential = principal_score - opponent_score

    # 5. Determine the winner and principal player's outcome.
    if principal_score > opponent_score:
        winner = principal_player
        outcome = GamePrincipalOutcome.WIN

    elif principal_score < opponent_score:
        winner = opponent_player
        outcome = GamePrincipalOutcome.LOSS

    else:
        winner = None
        outcome = GamePrincipalOutcome.TIE

    # 6. Establish the player counts for circular turn order.
    total_player_count = 5
    human_player_count = 2
    npc_player_count = total_player_count - human_player_count

    # 7. Calculate NPCs between principal and opponent.
    #
    # Count forward from the principal player's starting position
    # until reaching the opponent's starting position.
    #
    # Modulo accounts for wrapping from position 5 to position 1.
    npcs_after_principal = (
        opponent_turn_order - principal_turn_order - 1
    ) % total_player_count

    # 8. Calculate NPCs between opponent and principal.
    #
    # Count forward from the opponent's starting position
    # until reaching the principal player's starting position.
    npcs_before_principal = (
        principal_turn_order - opponent_turn_order - 1
    ) % total_player_count

    # 9. Determine whether principal directly precedes opponent.
    #
    # The principal directly precedes the opponent when
    # there are zero NPCs between them in circular turn order.
    principal_directly_precedes_opponent = (
        npcs_after_principal == 0
    )

    # 10. Assemble the research record.
    record = TurnOrderGameRecord(
        game_id=game.pk,
        date_played=game.date_played,

        principal_player=principal_player,
        opponent_player=opponent_player,

        principal_score=principal_score,
        opponent_score=opponent_score,

        principal_turn_order=principal_turn_order,
        opponent_turn_order=opponent_turn_order,

        winner=winner,
        outcome=outcome,
        score_differential=score_differential,

        npcs_after_principal=npcs_after_principal,
        npcs_before_principal=npcs_before_principal,
        principal_directly_precedes_opponent=(
            principal_directly_precedes_opponent
        ),
    )

    return record
