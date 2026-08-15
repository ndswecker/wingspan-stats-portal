from dataclasses import dataclass
import math
import statistics

from django.db.models import QuerySet

from ..models import GameResult


@dataclass(frozen=True)
class HistogramBin:
    lower_bound: int
    upper_bound: int
    games_played: int

@dataclass(frozen=True)
class NormalCurvePoint:
    score: float
    density: float

@dataclass(frozen=True)
class ScoreDistribution:
    games_played: int

    average_score: float
    median_score: float
    standard_deviation: float

    minimum_score: int
    maximum_score: int

    percentile_25: float
    percentile_75: float
    percentile_90: float

    histogram_bins: list[HistogramBin]
    normal_curve_points: list[NormalCurvePoint]

@dataclass(frozen=True)
class StatisticalComparison:
    label: str
    primary_value: float | None
    secondary_value: float | None
    difference: float | None
    percentage_difference: float | None

@dataclass(frozen=True)
class HistogramComparisonBin:
    lower_bound: int
    upper_bound: int
    primary_games_played: int
    secondary_games_played: int

    primary_density: float
    secondary_density: float

    primary_percentage: float
    secondary_percentage: float

@dataclass(frozen=True)
class ScoreDistributionComparison:
    histogram_bins: list[HistogramComparisonBin]
    primary_normal_curve_points: list[NormalCurvePoint]
    secondary_normal_curve_points: list[NormalCurvePoint]


def calculate_score_distribution(
        *,
        game_results: QuerySet[GameResult],
) -> ScoreDistribution:

    scores = list(
        game_results.values_list("score", flat=True)
    )

    if not scores:
        raise ValueError("No game results provided for score distribution calculation.")
    
    games_played = len(scores)
    average_score = statistics.mean(scores)
    median_score = statistics.median(scores)

    minimum_score = min(scores)
    maximum_score = max(scores)

    if games_played == 1:
        standard_deviation = 0.0
    else:
        standard_deviation = statistics.stdev(scores)

    percentile_25 = _calculate_percentile(
        scores=scores,
        percentile=0.25,
    )

    percentile_75 = _calculate_percentile(
        scores=scores,
        percentile=0.75,
    )

    percentile_90 = _calculate_percentile(
        scores=scores,
        percentile=0.90,
    )

    histogram_bins = _build_histogram_bins(
        scores=scores,
    )

    normal_curve_points = _build_normal_curve_points(
        average_score=average_score,
        standard_deviation=standard_deviation,
        histogram_bins=histogram_bins,
    )

    return ScoreDistribution(
        games_played=games_played,
        average_score=average_score,
        median_score=median_score,
        standard_deviation=standard_deviation,
        minimum_score=minimum_score,
        maximum_score=maximum_score,
        percentile_25=percentile_25,
        percentile_75=percentile_75,
        percentile_90=percentile_90,
        histogram_bins=histogram_bins,
        normal_curve_points=normal_curve_points,
    )


def _calculate_percentile(
        *,
        scores: list[int],
        percentile: float,
) -> float:
    """
    Calculate a percentile using linear interpolation between scores.

    The percentile is provided as a value between 0 and 1.
    For example, 0.25 represents the 25th percentile.
    """
    if not 0 <= percentile <= 1:
        raise ValueError("Percentile must be between 0 and 1.")

    # Percentiles depend on the position of values in an ordered dataset,
    # so the scores must first be sorted in ascending order.
    sorted_scores = sorted(scores)
    # Find the percentile's position in the sorted list of scores.
    # The posistion may fall between two actual observations.
    index = (len(sorted_scores) - 1) * percentile
    # Indentify the observations immediately below and above the percentile's position.
    lower_index = int(index)
    upper_index = min(lower_index + 1, len(sorted_scores) - 1)

    # Determine how far the percentile position lies between the lower and upper observations, and use that to interpolate a value.
    interpolation_weight = index - lower_index

    lower_score = sorted_scores[lower_index]
    upper_score = sorted_scores[upper_index]

    # Interpolate between the surrounding scores to estimate the 
    # score corresponding to the requested percentile.
    score_difference = upper_score - lower_score
    interpolated_difference = score_difference * interpolation_weight
    percentile_score = lower_score + interpolated_difference

    return percentile_score

def _build_histogram_bins(
    *,
    scores: list[int],
) -> list[HistogramBin]:
    if not scores:
        raise ValueError(
            "No scores provided for histogram bin calculation."
        )

    bin_width = 10

    minimum_score = min(scores)
    maximum_score = max(scores)

    first_bin_lower_bound = (
        minimum_score // bin_width
    ) * bin_width

    final_bin_lower_bound = (
        maximum_score // bin_width
    ) * bin_width

    histogram_bins = _build_histogram_bins_for_range(
        scores=scores,
        first_bin_lower_bound=first_bin_lower_bound,
        final_bin_lower_bound=final_bin_lower_bound,
        bin_width=bin_width,
    )

    return histogram_bins

def _build_normal_curve_points(
        *,
        average_score: float,
        standard_deviation: float,
        histogram_bins: list[HistogramBin],
) -> list[NormalCurvePoint]:
    """
    build points for a fitted normal-distribution reference curve.

    The curve uses the observed average score and sample standard deviation.
    It is intended only as a visual comparison against the histogram.
    """
    if not histogram_bins:
        raise ValueError("No histogram bins provided for normal curve calculation.")

    # A normal distribution cannot be calculated when the standard deviation 
    # is zero, which occurs when all scores are identical.
    if standard_deviation == 0:
        return []

    # Use the full histogram range so the curve and histogram share 
    # the same horizontal score range.
    minimum_score = histogram_bins[0].lower_bound
    maximum_score = histogram_bins[-1].upper_bound

    normal_curve_points = []

    # Generate one curve point per score value. Wingspan scores are 
    # integers, so this provides sufficient resolution for a smooth
    # visual curve without creating unnecessary data points.
    for score in range(minimum_score, maximum_score + 1):
        # Calculate the probability density of this score under a
        # normal distribution fitted to the observed dataset.
        exponent = -((score - average_score) ** 2) / (2 * (standard_deviation ** 2))
        density = (1 / (standard_deviation * (math.sqrt(2 * math.pi)))) * math.exp(exponent)

        normal_curve_points.append(
            NormalCurvePoint(
                score=float(score),
                density=density
            )
        )

    return normal_curve_points

def compare_score_distributions(
    *,
    primary_score_distribution: ScoreDistribution,
    secondary_score_distribution: ScoreDistribution,
) -> list[StatisticalComparison]:
    statistics = [
        (
            "Games Played",
            primary_score_distribution.games_played,
            secondary_score_distribution.games_played,
        ),
        (
            "Average Score",
            primary_score_distribution.average_score,
            secondary_score_distribution.average_score,
        ),
        (
            "Median Score",
            primary_score_distribution.median_score,
            secondary_score_distribution.median_score,
        ),
        (
            "Standard Deviation",
            primary_score_distribution.standard_deviation,
            secondary_score_distribution.standard_deviation,
        ),
        (
            "Minimum Score",
            primary_score_distribution.minimum_score,
            secondary_score_distribution.minimum_score,
        ),
        (
            "25th Percentile",
            primary_score_distribution.percentile_25,
            secondary_score_distribution.percentile_25,
        ),
        (
            "75th Percentile",
            primary_score_distribution.percentile_75,
            secondary_score_distribution.percentile_75,
        ),
        (
            "90th Percentile",
            primary_score_distribution.percentile_90,
            secondary_score_distribution.percentile_90,
        ),
        (
            "Maximum Score",
            primary_score_distribution.maximum_score,
            secondary_score_distribution.maximum_score,
        ),
    ]

    comparisons = []

    for label, primary_value, secondary_value in statistics:
        difference = primary_value - secondary_value

        percentage_difference = None

        if secondary_value != 0:
            percentage_difference = (
                difference
                / secondary_value
                * 100
            )

        comparisons.append(
            StatisticalComparison(
                label=label,
                primary_value=primary_value,
                secondary_value=secondary_value,
                difference=difference,
                percentage_difference=percentage_difference,
            )
        )

    return comparisons

def calculate_score_distribution_comparison(
    *,
    primary_game_results: QuerySet[GameResult],
    secondary_game_results: QuerySet[GameResult],
    primary_score_distribution: ScoreDistribution,
    secondary_score_distribution: ScoreDistribution,
) -> ScoreDistributionComparison:
    """
    Build comparison-ready histogram data for two players.

    Both players are placed into the same 10-point score bins so their
    distributions can share one histogram axis. Each player's counts are
    normalized independently into density values so differences in sample
    size do not distort the comparison. Normal reference curves are then
    generated across the same shared score range.
    """
    # Extract each player's raw scores so they can be redistributed
    # into one common set of histogram bins.
    primary_scores = list(
        primary_game_results.values_list(
            "score",
            flat=True,
        )
    )

    secondary_scores = list(
        secondary_game_results.values_list(
            "score",
            flat=True,
        )
    )

    if not primary_scores or not secondary_scores:
        raise ValueError(
            "Both players must have results for score distribution comparison."
        )

    bin_width = 10

    # The shared histogram range must cover the complete spread of both
    # players so neither distribution is truncated or independently scaled.
    combined_scores = (
        primary_scores
        + secondary_scores
    )

    minimum_score = min(combined_scores)
    maximum_score = max(combined_scores)

    first_bin_lower_bound = (
        minimum_score // bin_width
    ) * bin_width

    final_bin_lower_bound = (
        maximum_score // bin_width
    ) * bin_width

    # Build two separate histograms using the exact same score boundaries.
    # This guarantees that corresponding P1 and P2 bars represent the
    # same score interval when they are later overlaid in Plotly.
    primary_histogram_bins = _build_histogram_bins_for_range(
        scores=primary_scores,
        first_bin_lower_bound=first_bin_lower_bound,
        final_bin_lower_bound=final_bin_lower_bound,
        bin_width=bin_width,
    )

    secondary_histogram_bins = _build_histogram_bins_for_range(
        scores=secondary_scores,
        first_bin_lower_bound=first_bin_lower_bound,
        final_bin_lower_bound=final_bin_lower_bound,
        bin_width=bin_width,
    )

    if len(primary_histogram_bins) != len(secondary_histogram_bins):
        raise ValueError(
            "Primary and secondary histograms must contain the same number of bins."
        )

    comparison_bins = []

    # Combine the matching P1/P2 bins into one comparison record.
    # Counts remain available for tooltips, while density is used for
    # bar height so unequal sample sizes remain statistically comparable.
    for primary_bin, secondary_bin in zip(
        primary_histogram_bins,
        secondary_histogram_bins,
    ):
        if (
            primary_bin.lower_bound != secondary_bin.lower_bound
            or primary_bin.upper_bound != secondary_bin.upper_bound
        ):
            raise ValueError(
                "Primary and secondary histogram bins must match."
            )

        primary_density = (
            primary_bin.games_played
            / (
                primary_score_distribution.games_played
                * bin_width
            )
        )

        secondary_density = (
            secondary_bin.games_played
            / (
                secondary_score_distribution.games_played
                * bin_width
            )
        )

        primary_percentage = (
            primary_bin.games_played
            / primary_score_distribution.games_played
            * 100
        )

        secondary_percentage = (
            secondary_bin.games_played
            / secondary_score_distribution.games_played
            * 100
        )

        comparison_bin = HistogramComparisonBin(
            lower_bound=primary_bin.lower_bound,
            upper_bound=primary_bin.upper_bound,
            primary_games_played=primary_bin.games_played,
            secondary_games_played=secondary_bin.games_played,
            primary_density=primary_density,
            secondary_density=secondary_density,
            primary_percentage=primary_percentage,
            secondary_percentage=secondary_percentage,
        )

        comparison_bins.append(
            comparison_bin
        )

    # Each player keeps an independently fitted normal curve, but both
    # curves are evaluated across the same shared histogram range.
    primary_normal_curve_points = _build_normal_curve_points(
        average_score=primary_score_distribution.average_score,
        standard_deviation=primary_score_distribution.standard_deviation,
        histogram_bins=primary_histogram_bins,
    )

    secondary_normal_curve_points = _build_normal_curve_points(
        average_score=secondary_score_distribution.average_score,
        standard_deviation=secondary_score_distribution.standard_deviation,
        histogram_bins=secondary_histogram_bins,
    )

    score_distribution_comparison = ScoreDistributionComparison(
        histogram_bins=comparison_bins,
        primary_normal_curve_points=primary_normal_curve_points,
        secondary_normal_curve_points=secondary_normal_curve_points,
    )

    return score_distribution_comparison


def _build_histogram_bins_for_range(
    *,
    scores: list[int],
    first_bin_lower_bound: int,
    final_bin_lower_bound: int,
    bin_width: int = 10,
) -> list[HistogramBin]:
    histogram_bins = []

    current_lower_bound = first_bin_lower_bound

    while current_lower_bound <= final_bin_lower_bound:
        current_upper_bound = current_lower_bound + bin_width

        games_played_in_bin = sum(
            1
            for score in scores
            if current_lower_bound <= score < current_upper_bound
        )

        histogram_bins.append(
            HistogramBin(
                lower_bound=current_lower_bound,
                upper_bound=current_upper_bound,
                games_played=games_played_in_bin,
            )
        )

        current_lower_bound = current_upper_bound

    return histogram_bins
    