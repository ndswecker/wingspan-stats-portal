from dataclasses import dataclass
import math
import statistics

from django.db.models import QuerySet

from ..models import GameResult


@dataclass(frozen=True)
class HistogramBin:
    lower_bound: float
    upper_bound: float
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
        raise ValueError("No scores provided for histogram bin calculation.")

    bin_width = 10

    minimum_score = min(scores)
    maximum_score = max(scores)

    # Round the observed minimum down to the nearest multiple of the bin width
    # to determine the lower bound of the first histogram bin.
    first_bin_lower_bound = (minimum_score // bin_width) * bin_width

    # Build enough bins to include the observed maximum score.
    # The upper bound is exclusive, so a score of exactly 160 must 
    # fall into the 160-170 bin rather than ending the histogram at 160.
    final_bin_lower_bound = (maximum_score // bin_width) * bin_width

    histogram_bins = []

    current_lower_bound = first_bin_lower_bound
    while current_lower_bound <= final_bin_lower_bound:
        current_upper_bound = current_lower_bound + bin_width

        games_played_in_bin = sum(
            1 for score in scores
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