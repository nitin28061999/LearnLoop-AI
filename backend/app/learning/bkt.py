from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class BKTParameters:
    """Parameters controlling Bayesian Knowledge Tracing."""

    p_initial: float = 0.2
    p_learn: float = 0.1
    p_guess: float = 0.2
    p_slip: float = 0.1

    def __post_init__(self) -> None:
        for name, value in (
            ("p_initial", self.p_initial),
            ("p_learn", self.p_learn),
            ("p_guess", self.p_guess),
            ("p_slip", self.p_slip),
        ):
            if not isfinite(value) or not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1.")


def update_mastery(
    prior_mastery: float,
    is_correct: bool,
    parameters: BKTParameters = BKTParameters(),
) -> float:
    """Update concept mastery after one student response."""

    if not isfinite(prior_mastery) or not 0.0 <= prior_mastery <= 1.0:
        raise ValueError("prior_mastery must be between 0 and 1.")

    if not isinstance(is_correct, bool):
        raise ValueError("is_correct must be a boolean.")

    if is_correct:
        numerator = prior_mastery * (1.0 - parameters.p_slip)
        denominator = numerator + ((1.0 - prior_mastery) * parameters.p_guess)
    else:
        numerator = prior_mastery * parameters.p_slip
        denominator = numerator + ((1.0 - prior_mastery) * (1.0 - parameters.p_guess))

    if denominator == 0.0:
        raise ValueError("Cannot update mastery with zero evidence probability.")

    posterior = numerator / denominator

    updated_mastery = posterior + ((1.0 - posterior) * parameters.p_learn)

    return min(1.0, max(0.0, updated_mastery))
