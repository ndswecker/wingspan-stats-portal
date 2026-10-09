from dataclasses import dataclass
from datetime import date

from ...models import Player

from .turn_order_research import build_turn_order_dataset
from .turn_order_statistics import (
    TurnOrderComparisonStatistics,
    TurnOrderSignificanceResult,
    analyze_turn_order_comparison,
    analyze_turn_order_significance,
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