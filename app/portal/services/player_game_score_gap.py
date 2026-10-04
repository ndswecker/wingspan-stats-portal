from dataclasses import dataclass
from datetime import date
from statistics import mean, median

from django.db.models import Count, Prefetch, Q

from ..models import Game, GameResult, Player


@dataclass(frozen=True)
class GameScoreGap:
    """One shared game's score-gap data for the selected players."""

    game_id: int
    date_played: date
    primary_score: int
    secondary_score: int
    low_score: int
    high_score: int
    score_gap: int
    winner: Player | None

@dataclass(frozen=True)
class PlayerVictoryMarginSummary:
    """Victory-margin statistics for one player in the shared-game set."""

    player: Player
    wins: int
    losses: int
    win_rate_percent: float
    total_victory_margin: int
    average_victory_margin: float | None
    median_victory_margin: float | None

@dataclass(frozen=True)
class VictoryMarginInsight:
    """Plain-language interpretation of a victory-margin analysis."""

    summary: str
    frequency_insight: str
    margin_insight: str

@dataclass(frozen=True)
class VictoryMarginAnalysis:
    """Victory-margin comparison for the two selected players."""

    shared_games: int
    ties: int
    primary: PlayerVictoryMarginSummary
    secondary: PlayerVictoryMarginSummary
    insight: VictoryMarginInsight


def select_game_score_gaps(
    *,
    primary_player: Player,
    secondary_player: Player,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[GameScoreGap]:
    """
    Select shared games and calculate score-gap data for two players.

    A game qualifies when both selected players have a result in the game.
    Other players may also have participated. Optional date boundaries are
    inclusive.
    """
    games = (
        Game.objects
        # Count only results belonging to the two selected players. We do not
        # restrict the total result count because multiplayer games with
        # additional participants are valid for Game Score Gap.
        .annotate(
            selected_player_count=Count(
                "results",
                filter=Q(
                    results__player__in=[
                        primary_player,
                        secondary_player,
                    ]
                ),
            ),
        )
        .filter(
            selected_player_count=2,
        )
    )

    if start_date is not None:
        games = games.filter(
            date_played__gte=start_date,
        )

    if end_date is not None:
        games = games.filter(
            date_played__lte=end_date,
        )

    # Fetch only the two results needed by this feature. The GameResult model
    # guarantees one result per player per game, so each qualifying game will
    # provide exactly one primary and one secondary result here.
    selected_results = (
        GameResult.objects
        .filter(
            player__in=[
                primary_player,
                secondary_player,
            ],
        )
        .select_related("player")
    )

    games = (
        games
        .prefetch_related(
            Prefetch(
                "results",
                queryset=selected_results,
                to_attr="game_score_gap_results",
            )
        )
        # Score Gap is a game-by-game progression, so display the oldest game
        # first. Game ID provides deterministic ordering for same-day games.
        .order_by(
            "date_played",
            "id",
        )
    )

    score_gaps = []

    for game in games:
        results_by_player = {
            result.player_id: result
            for result in game.game_score_gap_results
        }

        primary_result = results_by_player[primary_player.id]
        secondary_result = results_by_player[secondary_player.id]

        primary_score = primary_result.score
        secondary_score = secondary_result.score

        low_score = min(
            primary_score,
            secondary_score,
        )
        high_score = max(
            primary_score,
            secondary_score,
        )

        if primary_score > secondary_score:
            winner = primary_player
        elif secondary_score > primary_score:
            winner = secondary_player
        else:
            winner = None

        score_gaps.append(
            GameScoreGap(
                game_id=game.id,
                date_played=game.date_played,
                primary_score=primary_score,
                secondary_score=secondary_score,
                low_score=low_score,
                high_score=high_score,
                score_gap=high_score - low_score,
                winner=winner,
            )
        )

    return score_gaps

def calculate_victory_margin_analysis(
    *,
    score_gaps: list[GameScoreGap],
    primary_player: Player,
    secondary_player: Player,
) -> VictoryMarginAnalysis:
    """
    Calculate victory-margin statistics from prepared shared-game score gaps.

    Win rate is calculated against all shared games, including ties. Victory
    margin statistics include only games won by the corresponding player.
    """
    shared_games = len(score_gaps)

    primary_victory_margins = [
        score_gap.score_gap
        for score_gap in score_gaps
        if (
            score_gap.winner is not None
            and score_gap.winner.id == primary_player.id
        )
    ]

    secondary_victory_margins = [
        score_gap.score_gap
        for score_gap in score_gaps
        if (
            score_gap.winner is not None
            and score_gap.winner.id == secondary_player.id
        )
    ]

    primary_wins = len(primary_victory_margins)
    secondary_wins = len(secondary_victory_margins)

    ties = (
        shared_games
        - primary_wins
        - secondary_wins
    )

    primary_summary = _build_player_victory_margin_summary(
        player=primary_player,
        victory_margins=primary_victory_margins,
        wins=primary_wins,
        losses=secondary_wins,
        shared_games=shared_games,
    )

    secondary_summary = _build_player_victory_margin_summary(
        player=secondary_player,
        victory_margins=secondary_victory_margins,
        wins=secondary_wins,
        losses=primary_wins,
        shared_games=shared_games,
    )

    insight = _build_victory_margin_insight(
        primary=primary_summary,
        secondary=secondary_summary,
    )

    return VictoryMarginAnalysis(
        shared_games=shared_games,
        ties=ties,
        primary=primary_summary,
        secondary=secondary_summary,
        insight=insight,
    )

def _build_player_victory_margin_summary(
    *,
    player: Player,
    victory_margins: list[int],
    wins: int,
    losses: int,
    shared_games: int,
) -> PlayerVictoryMarginSummary:
    """
    Build one player's victory-margin summary from their winning margins.
    """
    if shared_games == 0:
        win_rate_percent = 0.0
    else:
        win_rate_percent = (wins / shared_games) * 100

    if victory_margins:
        average_victory_margin = mean(victory_margins)
        median_victory_margin = median(victory_margins)
    else:
        average_victory_margin = None
        median_victory_margin = None

    return PlayerVictoryMarginSummary(
        player=player,
        wins=wins,
        losses=losses,
        win_rate_percent=win_rate_percent,
        total_victory_margin=sum(victory_margins),
        average_victory_margin=average_victory_margin,
        median_victory_margin=median_victory_margin,
    )

def _build_victory_margin_insight(
    *,
    primary: PlayerVictoryMarginSummary,
    secondary: PlayerVictoryMarginSummary,
) -> VictoryMarginInsight:
    """
    Build deterministic descriptive insight from victory-margin statistics.

    These statements describe observed results only. They do not imply
    statistical significance or predictive advantage.
    """
    if primary.win_rate_percent > secondary.win_rate_percent:
        frequency_insight = (
            f"{primary.player.name} has the higher win rate across the "
            "selected shared games."
        )
        frequency_winner = primary
    elif secondary.win_rate_percent > primary.win_rate_percent:
        frequency_insight = (
            f"{secondary.player.name} has the higher win rate across the "
            "selected shared games."
        )
        frequency_winner = secondary
    else:
        frequency_insight = (
            "Both players have the same win rate across the selected shared games."
        )
        frequency_winner = None

    primary_margin = primary.average_victory_margin
    secondary_margin = secondary.average_victory_margin

    if primary_margin is None and secondary_margin is None:
        margin_insight = (
            "Neither player has a victory margin in the selected shared games."
        )
        margin_winner = None

    elif secondary_margin is None:
        margin_insight = (
            f"Only {primary.player.name} has recorded a victory in the "
            "selected shared games."
        )
        margin_winner = primary

    elif primary_margin is None:
        margin_insight = (
            f"Only {secondary.player.name} has recorded a victory in the "
            "selected shared games."
        )
        margin_winner = secondary

    elif primary_margin > secondary_margin:
        margin_insight = (
            f"When {primary.player.name} wins, the average victory margin "
            f"is larger than {secondary.player.name}'s."
        )
        margin_winner = primary

    elif secondary_margin > primary_margin:
        margin_insight = (
            f"When {secondary.player.name} wins, the average victory margin "
            f"is larger than {primary.player.name}'s."
        )
        margin_winner = secondary

    else:
        margin_insight = (
            "Both players have the same average victory margin."
        )
        margin_winner = None

    if (
        frequency_winner is not None
        and margin_winner is not None
        and frequency_winner.player.id == margin_winner.player.id
    ):
        summary = (
            f"{frequency_winner.player.name} has both won more often "
            "and won by larger average margins."
        )

    elif frequency_winner is not None and margin_winner is not None:
        summary = (
            f"{frequency_winner.player.name} wins more often, while "
            f"{margin_winner.player.name} tends to win more decisively."
        )

    elif frequency_winner is not None:
        summary = (
            f"{frequency_winner.player.name} has the stronger win frequency, "
            "while average victory margins are even."
        )

    elif margin_winner is not None:
        summary = (
            f"Win frequency is even, while {margin_winner.player.name} "
            "has the larger average victory margin."
        )

    else:
        summary = (
            "The selected shared games show no advantage in win frequency "
            "or average victory margin."
        )

    return VictoryMarginInsight(
        summary=summary,
        frequency_insight=frequency_insight,
        margin_insight=margin_insight,
    )
