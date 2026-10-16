from dataclasses import dataclass
from datetime import date

from ...models import Player

from .turn_order_research import (
    build_turn_order_dataset,
    TurnOrderDataset,
    partition_direct_preceding_games,
)

from .turn_order_statistics import (
    TurnOrderComparisonStatistics,
    TurnOrderSignificanceResult,
    StartingPositionAnalysisStatistics,
    StartingPositionWinSignificanceResult,
    analyze_turn_order_comparison,
    analyze_turn_order_significance,
    analyze_starting_position_performance,
    analyze_starting_position_win_significance,
    analyze_starting_position_score_significance,
    analyze_starting_position_score_differential_significance,
    AnovaPermutationSignificanceResult,
    DirectPrecedingAnalysisStatistics,
    DirectPrecedingWinSignificanceResult,
    TwoSampleMeanPermutationSignificanceResult,
    analyze_direct_preceding_performance,
    analyze_direct_preceding_win_significance,
    analyze_direct_preceding_score_significance,
    analyze_direct_preceding_score_differential_significance,
)

@dataclass(frozen=True)
class TurnOrderComparisonResult:
    """
    Complete starting-order comparison between two players.

    Contains descriptive statistics and the results of
    the statistical significance test.
    """

    statistics: TurnOrderComparisonStatistics
    significance: TurnOrderSignificanceResult

@dataclass(frozen=True)
class StartingPositionAnalysisResult:
    """
    Combined descriptive and inferential results for the
    principal player's starting position.

    Covers Hypothesis 6.1 of the turn-order research methodology.
    """

    statistics: StartingPositionAnalysisStatistics
    win_significance: StartingPositionWinSignificanceResult
    score_significance: AnovaPermutationSignificanceResult
    score_differential_significance: AnovaPermutationSignificanceResult

@dataclass(frozen=True)
class DirectPrecedingAnalysisResult:
    """
    Combined descriptive and inferential results for
    the principal player directly preceding the opponent.

    Covers H2a, H2b, and H2c.
    """

    statistics: DirectPrecedingAnalysisStatistics
    win_significance: DirectPrecedingWinSignificanceResult
    score_significance: TwoSampleMeanPermutationSignificanceResult
    score_differential_significance: TwoSampleMeanPermutationSignificanceResult


def get_turn_order_comparison(
    *,
    principal_player: Player,
    opponent_player: Player,
    start_date: date | None = None,
    end_date: date | None = None,
) -> TurnOrderComparisonResult:
    """
    Retrieve qualifying games and analyze whether one player
    starts earlier than the other more frequently.

    Returns descriptive starting-position statistics and
    a two-sided exact binomial significance test.
    """

    # 1. Build the qualifying game dataset.
    dataset = build_turn_order_dataset(
        principal_player=principal_player,
        opponent_player=opponent_player,
        start_date=start_date,
        end_date=end_date,
    )

    # 2. Calculate descriptive starting-position statistics.
    statistics = analyze_turn_order_comparison(
        dataset=dataset,
    )

    # 3. Test the statistical significance of the starting-order imbalance.
    significance = analyze_turn_order_significance(
        statistics=statistics,
    )

    # 4. Assemble the complete research result.
    result = TurnOrderComparisonResult(
        statistics=statistics,
        significance=significance,
    )

    return result

def get_starting_position_analysis(
    *,
    dataset: TurnOrderDataset,
) -> StartingPositionAnalysisResult:
    """
    Run the starting-position research analysis.

    Includes descriptive statistics and significance tests
    for H1a, H1b, and H1c.

    Operates entirely on an existing in-memory dataset.
    """

    # 1. Calculate descriptive starting-position statistics.
    statistics = analyze_starting_position_performance(
        dataset=dataset,
    )

    # 2. Test H1a: Probability of winning.
    win_significance = analyze_starting_position_win_significance(
        statistics=statistics,
    )

    # 3. Test H1b: Average final score.
    score_significance = analyze_starting_position_score_significance(
        dataset=dataset,
    )

    # 4. Test H1c: Average score differential.
    score_differential_significance = (
        analyze_starting_position_score_differential_significance(
            dataset=dataset,
        )
    )

    # 5. Assemble the complete starting-position analysis.
    result = StartingPositionAnalysisResult(
        statistics=statistics,
        win_significance=win_significance,
        score_significance=score_significance,
        score_differential_significance=score_differential_significance,
    )

    return result

def get_direct_preceding_analysis(
    *,
    dataset: TurnOrderDataset,
) -> DirectPrecedingAnalysisResult:
    """
    Run the direct-preceding research analysis.

    Includes descriptive statistics and significance tests
    for H2a, H2b, and H2c.

    Operates entirely on an existing in-memory dataset.
    """

    # 1. Partition games by direct-preceding status.
    partition = partition_direct_preceding_games(
        dataset=dataset,
    )

    # 2. Calculate descriptive statistics.
    statistics = analyze_direct_preceding_performance(
        dataset=partition,
    )

    # 3. Test H2a: Probability of winning.
    win_significance = analyze_direct_preceding_win_significance(
        statistics=statistics,
    )

    # 4. Test H2b: Average final score.
    score_significance = analyze_direct_preceding_score_significance(
        dataset=partition,
    )

    # 5. Test H2c: Average score differential.
    score_differential_significance = (
        analyze_direct_preceding_score_differential_significance(
            dataset=partition,
        )
    )

    # 6. Assemble the complete H2 analysis.
    result = DirectPrecedingAnalysisResult(
        statistics=statistics,
        win_significance=win_significance,
        score_significance=score_significance,
        score_differential_significance=score_differential_significance,
    )

    return result