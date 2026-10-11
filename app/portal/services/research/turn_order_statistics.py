import numpy as np

from dataclasses import dataclass

from scipy.stats import binomtest

from .turn_order_research import TurnOrderDataset

from .statistical_methods import StatisticalTest

from .turn_order_research import (
    TurnOrderDataset,
    GamePrincipalOutcome,
)


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

@dataclass(frozen=True)
class StartingPositionPerformanceStatistics:
    """
    Descriptive performance statistics for the principal
    player at one starting position.
    """

    # Starting position being analyzed (1 through 5).
    position: int

    # Number of games played from this position.
    total_games: int

    # Game outcomes.
    wins: int
    losses: int
    ties: int
    win_rate: float | None

    # Scoring performance.
    average_score: float | None
    average_score_differential: float | None

@dataclass(frozen=True)
class StartingPositionAnalysisStatistics:
    """
    Descriptive performance statistics for the principal
    player across all five starting positions.
    """

    # Total number of qualifying games.
    total_games: int

    # Performance statistics indexed by starting position (1 through 5).
    positions: dict[int, StartingPositionPerformanceStatistics]

@dataclass(frozen=True)
class StartingPositionWinSignificanceResult:
    """Statistical significance of the association between starting position and winning."""

    test: StatisticalTest
    sample_size: int
    observed_statistic: float | None
    p_value: float | None
    significance_level: float
    is_significant: bool | None
    number_of_permutations: int
    random_seed: int

@dataclass(frozen=True)
class AnovaPermutationSignificanceResult:
    """
    Statistical significance of differences in group means
    using a one-way ANOVA permutation test.
    """

    test: StatisticalTest
    sample_size: int
    observed_statistic: float | None
    p_value: float | None
    significance_level: float
    is_significant: bool | None
    number_of_permutations: int
    random_seed: int


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

def analyze_starting_position_performance(
    *,
    dataset: TurnOrderDataset,
) -> StartingPositionAnalysisStatistics:
    """
    Calculate descriptive performance statistics for the
    principal player at each starting position (1 through 5).

    Calculates game outcomes, win rates, average scores,
    and average score differentials.

    Performs no database queries or hypothesis testing.
    """

    # 1. Determine the number of qualifying games.
    total_games = len(dataset.games)

    # 2. Initialize counters and running totals for each position.
    position_data = {}

    for position in range(1, 6):
        position_data[position] = {
            "total_games": 0,
            "wins": 0,
            "losses": 0,
            "ties": 0,
            "score_total": 0,
            "score_differential_total": 0,
        }

    # 3. Process each qualifying game.
    for game in dataset.games:

        # Identify the principal player's starting position.
        position = game.principal_turn_order
        data = position_data[position]

        # Count the game.
        data["total_games"] += 1

        # Count the game outcome.
        if game.outcome == GamePrincipalOutcome.WIN:
            data["wins"] += 1

        elif game.outcome == GamePrincipalOutcome.LOSS:
            data["losses"] += 1

        elif game.outcome == GamePrincipalOutcome.TIE:
            data["ties"] += 1

        # Accumulate scoring performance.
        data["score_total"] += game.principal_score
        data["score_differential_total"] += game.score_differential

    # 4. Calculate performance statistics for each position.
    positions = {}

    for position in range(1, 6):
        data = position_data[position]
        games_played = data["total_games"]

        # Initialize averages for positions with no games.
        win_rate = None
        average_score = None
        average_score_differential = None

        if games_played > 0:
            win_rate = data["wins"] / games_played
            average_score = data["score_total"] / games_played
            average_score_differential = (
                data["score_differential_total"] / games_played
            )

        # Assemble the statistics for this position.
        position_statistics = StartingPositionPerformanceStatistics(
            position=position,
            total_games=games_played,
            wins=data["wins"],
            losses=data["losses"],
            ties=data["ties"],
            win_rate=win_rate,
            average_score=average_score,
            average_score_differential=average_score_differential,
        )

        positions[position] = position_statistics

    # 5. Assemble the complete starting-position analysis.
    statistics = StartingPositionAnalysisStatistics(
        total_games=total_games,
        positions=positions,
    )

    return statistics


def analyze_starting_position_win_significance(
    *,
    statistics: StartingPositionAnalysisStatistics,
    significance_level: float = 0.05,
    number_of_permutations: int = 100_000,
    random_seed: int = 42,
) -> StartingPositionWinSignificanceResult:
    """
    Test whether the probability of winning differs across
    the principal player's five starting positions.

    Uses a Pearson chi-square statistic with a Monte Carlo
    permutation test.

    Null hypothesis:
        Win probability is equal across all five positions.

    Alternative hypothesis:
        Win probability differs for at least one position.

    Performs no database queries.
    """

    # 1. Identify the statistical test and sample size.
    test = StatisticalTest.PEARSON_CHI_SQUARE_PERMUTATION
    sample_size = statistics.total_games

    if number_of_permutations < 1:
        raise ValueError("number_of_permutations must be positive.")

    # 2. Collect observed wins and non-wins by position.
    position_counts = np.array(
        [statistics.positions[position].total_games for position in range(1, 6)],
        dtype=int,
    )

    observed_wins = np.array(
        [statistics.positions[position].wins for position in range(1, 6)],
        dtype=int,
    )

    total_wins = int(observed_wins.sum())
    total_non_wins = sample_size - total_wins

    # 3. Initialize results for cases where testing is not possible.
    observed_statistic = None
    p_value = None
    is_significant = None

    # 4. Test only when both outcomes occur and at least
    #    two starting positions have observations.
    if (
        total_wins > 0
        and total_non_wins > 0
        and np.count_nonzero(position_counts) >= 2
    ):

        # Exclude positions with no observed games.
        active_counts = position_counts[position_counts > 0]
        active_wins = observed_wins[position_counts > 0]

        # 5. Calculate expected wins and non-wins under H0.
        expected_wins = active_counts * total_wins / sample_size
        expected_non_wins = active_counts * total_non_wins / sample_size

        # 6. Calculate the observed Pearson chi-square statistic.
        observed_non_wins = active_counts - active_wins

        observed_statistic = float(
            np.sum((active_wins - expected_wins) ** 2 / expected_wins)
            + np.sum(
                (observed_non_wins - expected_non_wins) ** 2
                / expected_non_wins
            )
        )

        # 7. Construct the outcomes and position assignments.
        outcomes = np.array(
            [1] * total_wins + [0] * total_non_wins,
            dtype=int,
        )

        position_indices = np.repeat(
            np.arange(len(active_counts)),
            active_counts,
        )

        # 8. Generate reproducible random permutations.
        rng = np.random.default_rng(random_seed)
        extreme_count = 0

        for _ in range(number_of_permutations):
            shuffled_outcomes = rng.permutation(outcomes)

            permuted_wins = np.bincount(
                position_indices,
                weights=shuffled_outcomes,
                minlength=len(active_counts),
            )

            permuted_non_wins = active_counts - permuted_wins

            permuted_statistic = (
                np.sum(
                    (permuted_wins - expected_wins) ** 2
                    / expected_wins
                )
                + np.sum(
                    (permuted_non_wins - expected_non_wins) ** 2
                    / expected_non_wins
                )
            )

            # Count permutations at least as extreme as observed.
            if permuted_statistic >= observed_statistic - 1e-12:
                extreme_count += 1

        # 9. Estimate the permutation p-value.
        #    The +1 correction avoids reporting a zero p-value.
        p_value = (extreme_count + 1) / (number_of_permutations + 1)
        is_significant = p_value < significance_level

    # 10. Assemble the statistical result.
    return StartingPositionWinSignificanceResult(
        test=test,
        sample_size=sample_size,
        observed_statistic=observed_statistic,
        p_value=p_value,
        significance_level=significance_level,
        is_significant=is_significant,
        number_of_permutations=number_of_permutations,
        random_seed=random_seed,
    )


def _calculate_anova_f_statistic(
    *,
    values: np.ndarray,
    group_indices: np.ndarray,
    group_sizes: np.ndarray,
) -> float:
    """
    Calculate the one-way ANOVA F-statistic for numerical
    observations assigned to categorical groups.

    Performs no database queries or permutation testing.
    """

    # 1. Calculate sample size and degrees of freedom.
    sample_size = len(values)
    number_of_groups = len(group_sizes)

    between_df = number_of_groups - 1
    within_df = sample_size - number_of_groups

    # 2. Calculate the overall mean.
    grand_mean = np.mean(values)

    # 3. Calculate the mean for each group.
    group_sums = np.bincount(
        group_indices,
        weights=values,
        minlength=number_of_groups,
    )

    group_means = group_sums / group_sizes

    # 4. Calculate variation between group means.
    between_ss = np.sum(
        group_sizes * (group_means - grand_mean) ** 2
    )

    # 5. Calculate variation within groups.
    within_ss = np.sum(
        (values - group_means[group_indices]) ** 2
    )

    # 6. Handle cases with no within-group variation.
    if within_ss == 0:
        return float("inf") if between_ss > 0 else 0.0

    # 7. Calculate the ANOVA F-statistic.
    f_statistic = (
        (between_ss / between_df)
        / (within_ss / within_df)
    )

    return float(f_statistic)


def analyze_anova_permutation_significance(
    *,
    groups: dict[int, list[int]],
    significance_level: float = 0.05,
    number_of_permutations: int = 100_000,
    random_seed: int = 42,
) -> AnovaPermutationSignificanceResult:
    """
    Test whether mean numerical outcomes differ across
    starting positions using a one-way ANOVA F-statistic
    and Monte Carlo permutation testing.

    The groups dictionary maps starting positions 1 through 5
    to individual game observations.

    Performs no database queries.
    """

    # 1. Validate statistical test parameters.
    if not 0 < significance_level < 1:
        raise ValueError("significance_level must be between 0 and 1.")

    if number_of_permutations < 1:
        raise ValueError("number_of_permutations must be positive.")

    # 2. Collect observations for the five starting positions.
    group_arrays = [
        np.asarray(groups[position], dtype=float)
        for position in range(1, 6)
    ]

    active_groups = [
        group for group in group_arrays
        if len(group) > 0
    ]

    sample_size = sum(len(group) for group in active_groups)

    # 3. Initialize results for cases where testing is not possible.
    observed_statistic = None
    p_value = None
    is_significant = None

    # 4. Require at least two represented positions and
    #    sufficient observations for residual degrees of freedom.
    if len(active_groups) >= 2 and sample_size > len(active_groups):

        group_sizes = np.array(
            [len(group) for group in active_groups],
            dtype=int,
        )

        observations = np.concatenate(active_groups)

        group_indices = np.repeat(
            np.arange(len(active_groups)),
            group_sizes,
        )

        # 5. Calculate the observed ANOVA F-statistic.
        observed_statistic = _calculate_anova_f_statistic(
            values=observations,
            group_indices=group_indices,
            group_sizes=group_sizes,
        )

        # 6. Generate the permutation null distribution.
        rng = np.random.default_rng(random_seed)
        extreme_count = 0

        for _ in range(number_of_permutations):
            permuted_values = rng.permutation(observations)

            permuted_statistic = _calculate_anova_f_statistic(
                values=permuted_values,
                group_indices=group_indices,
                group_sizes=group_sizes,
            )

            # Count permutations at least as extreme as observed.
            if permuted_statistic >= observed_statistic - 1e-12:
                extreme_count += 1

        # 7. Calculate the Monte Carlo p-value.
        p_value = (extreme_count + 1) / (number_of_permutations + 1)
        is_significant = p_value < significance_level

    # 8. Assemble the statistical result.
    return AnovaPermutationSignificanceResult(
        test=StatisticalTest.ONE_WAY_ANOVA_PERMUTATION,
        sample_size=sample_size,
        observed_statistic=observed_statistic,
        p_value=p_value,
        significance_level=significance_level,
        is_significant=is_significant,
        number_of_permutations=number_of_permutations,
        random_seed=random_seed,
    )


def analyze_starting_position_score_significance(
    *,
    dataset: TurnOrderDataset,
    significance_level: float = 0.05,
    number_of_permutations: int = 100_000,
    random_seed: int = 42,
) -> AnovaPermutationSignificanceResult:
    """
    H1b: Test whether the principal player's mean final score
    differs across starting positions.

    Uses individual game scores, not group averages.
    """

    # 1. Initialize observations for all five starting positions.
    groups = {
        position: []
        for position in range(1, 6)
    }

    # 2. Group individual final scores by starting position.
    for game in dataset.games:
        groups[game.principal_turn_order].append(
            game.principal_score
        )

    # 3. Perform the one-way ANOVA permutation test.
    return analyze_anova_permutation_significance(
        groups=groups,
        significance_level=significance_level,
        number_of_permutations=number_of_permutations,
        random_seed=random_seed,
    )


def analyze_starting_position_score_differential_significance(
    *,
    dataset: TurnOrderDataset,
    significance_level: float = 0.05,
    number_of_permutations: int = 100_000,
    random_seed: int = 42,
) -> AnovaPermutationSignificanceResult:
    """
    H1c: Test whether the principal player's mean score
    differential differs across starting positions.

    Uses individual game score differentials.
    """

    # 1. Initialize observations for all five starting positions.
    groups = {
        position: []
        for position in range(1, 6)
    }

    # 2. Group individual score differentials by starting position.
    for game in dataset.games:
        groups[game.principal_turn_order].append(
            game.score_differential
        )

    # 3. Perform the one-way ANOVA permutation test.
    return analyze_anova_permutation_significance(
        groups=groups,
        significance_level=significance_level,
        number_of_permutations=number_of_permutations,
        random_seed=random_seed,
    )

