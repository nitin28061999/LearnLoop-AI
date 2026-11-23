
from datetime import UTC, datetime, timedelta

import pytest

from app.learning.spaced_repetition import (  # pyright: ignore[reportMissingImports]
    ReviewState,
    schedule_next_review,
)

NOW = datetime(2026, 11, 22, 12, 0, tzinfo=UTC)


def test_first_correct_answer_schedules_review_after_one_day():
    result = schedule_next_review(
        state=ReviewState(),
        is_correct=True,
        reviewed_at=NOW,
    )

    assert result.repetition_count == 1
    assert result.interval_days == 1
    assert result.ease_factor == pytest.approx(2.6)
    assert result.next_review_at == NOW + timedelta(days=1)


def test_second_consecutive_correct_answer_schedules_three_days():
    previous = ReviewState(
        repetition_count=1,
        interval_days=1,
        ease_factor=2.6,
        next_review_at=NOW,
        last_reviewed_at=NOW - timedelta(days=1),
    )

    result = schedule_next_review(
        state=previous,
        is_correct=True,
        reviewed_at=NOW,
    )

    assert result.repetition_count == 2
    assert result.interval_days == 3
    assert result.ease_factor == pytest.approx(2.7)
    assert result.next_review_at == NOW + timedelta(days=3)


def test_subsequent_correct_answer_uses_previous_interval():
    previous = ReviewState(
        repetition_count=2,
        interval_days=3,
        ease_factor=2.7,
        next_review_at=NOW,
        last_reviewed_at=NOW - timedelta(days=3),
    )

    result = schedule_next_review(
        state=previous,
        is_correct=True,
        reviewed_at=NOW,
    )

    assert result.repetition_count == 3
    assert result.interval_days == 8
    assert result.ease_factor == pytest.approx(2.8)
    assert result.next_review_at == NOW + timedelta(days=8)


def test_incorrect_answer_resets_repetition_streak():
    previous = ReviewState(
        repetition_count=4,
        interval_days=12,
        ease_factor=2.5,
        next_review_at=NOW,
        last_reviewed_at=NOW - timedelta(days=12),
    )

    result = schedule_next_review(
        state=previous,
        is_correct=False,
        reviewed_at=NOW,
    )

    assert result.repetition_count == 0
    assert result.interval_days == 1
    assert result.ease_factor == pytest.approx(2.3)
    assert result.next_review_at == NOW + timedelta(days=1)


def test_ease_factor_never_falls_below_minimum():
    previous = ReviewState(
        repetition_count=0,
        interval_days=1,
        ease_factor=1.3,
        next_review_at=NOW,
        last_reviewed_at=NOW - timedelta(days=1),
    )

    result = schedule_next_review(
        state=previous,
        is_correct=False,
        reviewed_at=NOW,
    )

    assert result.ease_factor == pytest.approx(1.3)


def test_reviewed_at_must_be_timezone_aware():
    with pytest.raises(ValueError, match="timezone"): # pyright: ignore[reportGeneralTypeIssues]
        schedule_next_review(
            state=ReviewState(),
            is_correct=True,
            reviewed_at=datetime(2026, 11, 22, 12, 0),
        )
def test_rejects_non_boolean_correctness():
    with pytest.raises(ValueError, match="boolean"):
        schedule_next_review(
            state=ReviewState(),
            is_correct=1, # pyright: ignore[reportArgumentType]
            reviewed_at=NOW,
        )


def test_rejects_negative_repetition_count():
    with pytest.raises(ValueError, match="repetition_count"):
        schedule_next_review(
            state=ReviewState(repetition_count=-1),
            is_correct=True,
            reviewed_at=NOW,
        )


def test_rejects_negative_interval():
    with pytest.raises(ValueError, match="interval_days"):
        schedule_next_review(
            state=ReviewState(interval_days=-1),
            is_correct=True,
            reviewed_at=NOW,
        )


def test_rejects_invalid_ease_factor():
    with pytest.raises(ValueError, match="ease_factor"):
        schedule_next_review(
            state=ReviewState(ease_factor=1.0),
            is_correct=True,
            reviewed_at=NOW,
        )


def test_rejects_non_finite_ease_factor():
    with pytest.raises(ValueError, match="ease_factor"):
        schedule_next_review(
            state=ReviewState(ease_factor=float("inf")),
            is_correct=True,
            reviewed_at=NOW,
        )
