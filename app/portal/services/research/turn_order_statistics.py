from dataclasses import dataclass

from scipy.stats import binomtest

from .turn_order_research import TurnOrderDataset

from .statistical_methods import StatisticalTest


@dataclass(frozen=True)
class PlayerTurnOrderStatistics:
    """
    Descriptive starting-position statistics for one player.
    """

    # Average numerical starting position across qualifying games.
    average_turn_order: float | None

    # Number of games started in each position (1 through 5).
    position_counts: dict[int, int]


@dataclass(frozen=True)
class TurnOrderComparisonStatistics:
    """
    Starting-position comparison between the principal player
    and the opponent.
    """

    # Total number of qualifying games analyzed.
    total_games: int

    # Individual starting-position statistics for each player.
    principal: PlayerTurnOrderStatistics
    opponent: PlayerTurnOrderStatistics

    # Number of games where principal had a lower turn-order number.
    principal_starts_earlier: int

    # Number of games where opponent had a lower turn-order number.
    opponent_starts_earlier: int

@dataclass(frozen=True)
class TurnOrderSignificanceResult:
    """
    Statistical significance of the head-to-head
    starting-order imbalance.
    """

    # Statistical test used, including its name and methodology.
    test: StatisticalTest

    # Inputs used in the statistical test.
    sample_size: int
    principal_starts_earlier: int
    opponent_starts_earlier: int
    expected_probability: float

    # Statistical results.
    p_value: float | None
    significance_level: float
    is_significant: bool


def analyze_turn_order_comparison(
    *,
    dataset: TurnOrderDataset,
) -> TurnOrderComparisonStatistics:
    """
    Calculate descriptive starting-position statistics for the
    principal player and opponent.

    Calculates average starting positions, starting-position
    frequencies, and how often each player starts earlier
    than the other.

    Performs no database queries or hypothesis testing.
    """

    # 1. Determine the number of qualifying games.
    total_games = len(dataset.games)

    # 2. Initialize starting-position counters for both players.
    principal_position_counts = {}
    opponent_position_counts = {}

    for position in range(1, 6):
        principal_position_counts[position] = 0
        opponent_position_counts[position] = 0

    # 3. Initialize running totals for average calculations.
    principal_turn_order_total = 0
    opponent_turn_order_total = 0

    # 4. Initialize head-to-head starting-order counters.
    principal_starts_earlier = 0
    opponent_starts_earlier = 0

    # 5. Process each qualifying game.
    for game in dataset.games:

        # Retrieve each player's starting position.
        principal_position = game.principal_turn_order
        opponent_position = game.opponent_turn_order

        # Count how often each player starts in each position.
        principal_position_counts[principal_position] += 1
        opponent_position_counts[opponent_position] += 1

        # Accumulate starting positions for average calculations.
        principal_turn_order_total += principal_position
        opponent_turn_order_total += opponent_position

        # Determine which player starts earlier.
        if principal_position < opponent_position:
            principal_starts_earlier += 1

        elif opponent_position < principal_position:
            opponent_starts_earlier += 1

    # 6. Calculate average starting positions.
    principal_average = None
    opponent_average = None

    if total_games > 0:
        principal_average = principal_turn_order_total / total_games
        opponent_average = opponent_turn_order_total / total_games

    # 7. Assemble principal player statistics.
    principal_statistics = PlayerTurnOrderStatistics(
        average_turn_order=principal_average,
        position_counts=principal_position_counts,
    )

    # 8. Assemble opponent player statistics.
    opponent_statistics = PlayerTurnOrderStatistics(
        average_turn_order=opponent_average,
        position_counts=opponent_position_counts,
    )

    # 9. Assemble the complete comparison statistics.
    statistics = TurnOrderComparisonStatistics(
        total_games=total_games,
        principal=principal_statistics,
        opponent=opponent_statistics,
        principal_starts_earlier=principal_starts_earlier,
        opponent_starts_earlier=opponent_starts_earlier,
    )

    return statistics

def analyze_turn_order_significance(
    *,
    statistics: TurnOrderComparisonStatistics,
    significance_level: float = 0.05,
) -> TurnOrderSignificanceResult:
    """
    Test whether the principal player starts earlier than
    the opponent significantly more or less often than chance.

    Uses a two-sided exact binomial test.

    Null hypothesis:
        The principal player has a 50% probability of
        starting earlier than the opponent.

    Alternative hypothesis:
        The probability differs from 50%.

    Performs no database queries.
    """

    # 1. Identify the statistical test and its parameters.
    test = StatisticalTest.EXACT_BINOMIAL_TWO_SIDED
    expected_probability = 0.5

    # 2. Retrieve the observed starting-order counts.
    total_games = statistics.total_games
    principal_starts_earlier = statistics.principal_starts_earlier
    opponent_starts_earlier = statistics.opponent_starts_earlier

    # 3. Initialize the statistical result.
    p_value = None
    is_significant = False

    # 4. Perform the statistical test when games are available.
    if total_games > 0:

        test_result = binomtest(
            k=principal_starts_earlier,
            n=total_games,
            p=expected_probability,
            alternative="two-sided",
        )

        p_value = float(test_result.pvalue)

        # Determine statistical significance.
        is_significant = p_value < significance_level

    # 5. Assemble the significance result.
    result = TurnOrderSignificanceResult(
        test=test,
        sample_size=total_games,
        principal_starts_earlier=principal_starts_earlier,
        opponent_starts_earlier=opponent_starts_earlier,
        expected_probability=expected_probability,
        p_value=p_value,
        significance_level=significance_level,
        is_significant=is_significant,
    )

    return result