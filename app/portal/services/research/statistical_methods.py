from enum import StrEnum


class StatisticalTest(StrEnum):
    """
    Statistical tests supported by the research portal.
    """

    EXACT_BINOMIAL_TWO_SIDED = (
        "exact_binomial_two_sided",
        "Two-sided exact binomial test",
        "Tests whether the probability of one of two possible "
        "outcomes differs from an expected probability."
    )

    PEARSON_CHI_SQUARE_PERMUTATION = (
        "pearson_chi_square_permutation",
        "Pearson chi-square permutation test",
        "Tests whether two categorical variables are associated "
        "by comparing the observed Pearson chi-square statistic "
        "against a permutation-based null distribution.",
    )

    ONE_WAY_ANOVA_PERMUTATION = (
        "one_way_anova_permutation",
        "One-way ANOVA permutation test",
        "Tests whether mean numerical outcomes differ across categorical "
        "groups using the one-way ANOVA F-statistic and a "
        "permutation-based null distribution.",
    )

    def __new__(cls, value, display_name, description):
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj.display_name = display_name
        obj.description = description
        return obj