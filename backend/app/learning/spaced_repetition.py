from dataclasses import dataclass
from datetime import datetime, timedelta
from math import isfinite

MIN_EASE_FACTOR = 1.3
INITIAL_EASE_FACTOR = 2.5
EASE_INCREMENT = 0.1
EASE_DECREMENT = 0.2


@dataclass(frozen=True)
class ReviewState:
    repetition_count: int = 0
    interval_days: int = 0
    ease_factor: float = INITIAL_EASE_FACTOR
    next_review_at: datetime | None = None
    last_reviewed_at: datetime | None = None


def schedule_next_review(
    state: ReviewState,
    is_correct: bool,
    reviewed_at: datetime,
) -> ReviewState:
    """Calculate the next review using a binary SM-2-inspired policy."""
    if not isinstance(is_correct, bool):
        raise ValueError("is_correct must be a boolean.")

    if reviewed_at.tzinfo is None or reviewed_at.utcoffset() is None:
        raise ValueError("reviewed_at must be timezone-aware.")

    if (
        not isinstance(state.repetition_count, int)
        or isinstance(state.repetition_count, bool)
        or state.repetition_count < 0
    ):
        raise ValueError("repetition_count must be a non-negative integer.")

    if (
        not isinstance(state.interval_days, int)
        or isinstance(state.interval_days, bool)
        or state.interval_days < 0
    ):
        raise ValueError("interval_days must be a non-negative integer.")

    if (
        not isfinite(state.ease_factor)
        or state.ease_factor < MIN_EASE_FACTOR
    ):
        raise ValueError(
            f"ease_factor must be finite and at least {MIN_EASE_FACTOR}."
        )

    if is_correct:
        repetition_count = state.repetition_count + 1

        if repetition_count == 1:
            interval_days = 1
        elif repetition_count == 2:
            interval_days = 3
        else:
            interval_days = max(1, round(state.interval_days * state.ease_factor))

        ease_factor = state.ease_factor + EASE_INCREMENT
    else:
        repetition_count = 0
        interval_days = 1
        ease_factor = max(
            MIN_EASE_FACTOR,
            state.ease_factor - EASE_DECREMENT,
        )

    return ReviewState(
        repetition_count=repetition_count,
        interval_days=interval_days,
        ease_factor=ease_factor,
        next_review_at=reviewed_at + timedelta(days=interval_days),
        last_reviewed_at=reviewed_at,
    )
