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

    def __new__(cls, value, display_name, description):
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj.display_name = display_name
        obj.description = description
        return obj