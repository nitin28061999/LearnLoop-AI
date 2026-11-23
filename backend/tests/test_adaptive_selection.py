
from datetime import UTC, datetime, timedelta

import pytest  # pyright: ignore[reportMissingImports]

from app.learning.adaptive import (  # pyright: ignore[reportMissingImports]
    QuestionCandidate,
    select_adaptive_question,
    target_difficulty,
)


def make_question(
    question_id,
    concept_id,
    difficulty,
    question_text=None,
):
    return QuestionCandidate(
        question_id=question_id,
        concept_id=concept_id,
        question_text=question_text or f"Question {question_id}",
        difficulty=difficulty,
    )


def test_weakest_concept_is_prioritized():
    questions = [
        make_question("q1", "concept-strong", 1),
        make_question("q2", "concept-weak", 1),
    ]

    result = select_adaptive_question(
        questions,
        mastery_by_concept={
            "concept-strong": 0.8,
            "concept-weak": 0.2,
        },
    )

    assert result.question_id == "q2" # pyright: ignore[reportOptionalMemberAccess]


def test_question_difficulty_matches_student_mastery():
    questions = [
        make_question("q1", "concept-1", 1),
        make_question("q2", "concept-1", 3),
        make_question("q3", "concept-1", 5),
    ]

    result = select_adaptive_question(
        questions,
        mastery_by_concept={"concept-1": 0.6},
    )

    assert result.question_id == "q2" # pyright: ignore[reportOptionalMemberAccess]


def test_unattempted_question_is_preferred():
    questions = [
        make_question("q1", "concept-1", 1, "Previously attempted"),
        make_question("q2", "concept-1", 1, "New question"),
    ]

    result = select_adaptive_question(
        questions,
        mastery_by_concept={"concept-1": 0.2},
        attempted_question_texts={"Previously attempted"},
    )

    assert result.question_id == "q2" # pyright: ignore[reportOptionalMemberAccess]


def test_nearest_available_difficulty_is_selected():
    questions = [
        make_question("q1", "concept-1", 1),
        make_question("q2", "concept-1", 4),
    ]

    result = select_adaptive_question(
        questions,
        mastery_by_concept={"concept-1": 0.6},
    )

    assert result.question_id == "q2" # pyright: ignore[reportOptionalMemberAccess]


def test_empty_question_pool_returns_none():
    result = select_adaptive_question(
        [],
        mastery_by_concept={},
    )

    assert result is None


@pytest.mark.parametrize(
    ("mastery", "expected"),
    [
        (0.0, 1),
        (0.29, 1),
        (0.30, 2),
        (0.49, 2),
        (0.50, 3),
        (0.69, 3),
        (0.70, 4),
        (0.84, 4),
        (0.85, 5),
        (1.0, 5),
    ],
)
def test_target_difficulty_boundaries(mastery, expected):
    assert target_difficulty(mastery) == expected


@pytest.mark.parametrize("mastery", [-0.1, 1.1, float("nan"), float("inf")])
def test_target_difficulty_rejects_invalid_mastery(mastery):
    with pytest.raises(ValueError):
        target_difficulty(mastery)


def test_selector_rejects_invalid_question_difficulty():
    questions = [make_question("q1", "concept-1", 6)]

    with pytest.raises(ValueError, match="difficulty"):
        select_adaptive_question(
            questions,
            mastery_by_concept={"concept-1": 0.2},
        )


def test_selector_rejects_invalid_mastery():
    questions = [make_question("q1", "concept-1", 1)]

    with pytest.raises(ValueError, match="Invalid mastery"):
        select_adaptive_question(
            questions,
            mastery_by_concept={"concept-1": 1.5},
        )


def test_returns_question_when_all_questions_were_attempted():
    questions = [
        make_question("q1", "concept-1", 1, "Question one"),
        make_question("q2", "concept-1", 1, "Question two"),
    ]

    result = select_adaptive_question(
        questions,
        mastery_by_concept={"concept-1": 0.2},
        attempted_question_texts={"Question one", "Question two"},
    )

    assert result is not None
    assert result.question_id == "q1"


def test_missing_mastery_uses_initial_bkt_probability():
    questions = [
        make_question("q1", "concept-1", 1),
        make_question("q2", "concept-2", 1),
    ]

    result = select_adaptive_question(
        questions,
        mastery_by_concept={"concept-2": 0.8},
    )

    assert result is not None
    assert result.question_id == "q1"


def test_question_for_concept_is_blocked_until_prerequisite_is_mastered():
    questions = [
        make_question("q1", "foundation", 1),
        make_question("q2", "advanced", 2),
    ]

    result = select_adaptive_question(
        questions,
        mastery_by_concept={
            "foundation": 0.5,
            "advanced": 0.2,
        },
        prerequisites_by_concept={
            "advanced": {"foundation"},
        },
    )

    assert result is not None
    assert result.question_id == "q1"


def test_question_becomes_eligible_when_prerequisite_reaches_threshold():
    questions = [
        make_question("q1", "foundation", 3),
        make_question("q2", "advanced", 1),
    ]

    result = select_adaptive_question(
        questions,
        mastery_by_concept={
            "foundation": 0.70,
            "advanced": 0.2,
        },
        prerequisites_by_concept={
            "advanced": {"foundation"},
        },
    )

    assert result is not None
    assert result.question_id == "q2"


def test_concept_is_blocked_when_any_prerequisite_is_not_mastered():
    questions = [
        make_question("q1", "advanced", 1),
    ]

    result = select_adaptive_question(
        questions,
        mastery_by_concept={
            "foundation-1": 0.9,
            "foundation-2": 0.69,
            "advanced": 0.2,
        },
        prerequisites_by_concept={
            "advanced": {"foundation-1", "foundation-2"},
        },
    )

    assert result is None


def test_missing_prerequisite_mastery_uses_initial_bkt_probability():
    questions = [
        make_question("q1", "advanced", 1),
    ]

    result = select_adaptive_question(
        questions,
        mastery_by_concept={},
        prerequisites_by_concept={
            "advanced": {"foundation"},
        },
    )

    assert result is None


def test_due_review_concept_is_prioritized_over_weaker_future_review():
    now = datetime(2026, 11, 22, 12, 0, tzinfo=UTC)

    questions = [
        make_question("q1", "weak-concept", 1),
        make_question("q2", "due-concept", 2),
    ]

    result = select_adaptive_question(
        questions,
        mastery_by_concept={
            "weak-concept": 0.10,
            "due-concept": 0.60,
        },
        next_review_by_concept={
            "weak-concept": now + timedelta(days=3),
            "due-concept": now - timedelta(days=1),
        },
        current_time=now,
    )

    assert result is not None
    assert result.question_id == "q2"


def test_review_due_exactly_at_current_time_is_prioritized():
    now = datetime(2026, 11, 22, 12, 0, tzinfo=UTC)

    questions = [
        make_question("q1", "future-concept", 1),
        make_question("q2", "due-concept", 2),
    ]

    result = select_adaptive_question(
        questions,
        mastery_by_concept={
            "future-concept": 0.10,
            "due-concept": 0.60,
        },
        next_review_by_concept={
            "future-concept": now + timedelta(seconds=1),
            "due-concept": now,
        },
        current_time=now,
    )

    assert result is not None
    assert result.question_id == "q2"


def test_most_overdue_concept_is_prioritized():
    now = datetime(2026, 11, 22, 12, 0, tzinfo=UTC)

    questions = [
        make_question("q1", "recently-due", 1),
        make_question("q2", "long-overdue", 1),
    ]

    result = select_adaptive_question(
        questions,
        mastery_by_concept={
            "recently-due": 0.10,
            "long-overdue": 0.60,
        },
        next_review_by_concept={
            "recently-due": now - timedelta(days=1),
            "long-overdue": now - timedelta(days=5),
        },
        current_time=now,
    )

    assert result is not None
    assert result.question_id == "q2"


def test_future_review_does_not_override_weakest_concept():
    now = datetime(2026, 11, 22, 12, 0, tzinfo=UTC)

    questions = [
        make_question("q1", "strong-concept", 1),
        make_question("q2", "weak-concept", 1),
    ]

    result = select_adaptive_question(
        questions,
        mastery_by_concept={
            "strong-concept": 0.80,
            "weak-concept": 0.20,
        },
        next_review_by_concept={
            "strong-concept": now + timedelta(days=5),
            "weak-concept": now + timedelta(days=2),
        },
        current_time=now,
    )

    assert result is not None
    assert result.question_id == "q2"


def test_selector_rejects_naive_next_review_timestamp():
    questions = [make_question("q1", "concept-1", 1)]

    with pytest.raises(ValueError, match="Invalid next review time"):
        select_adaptive_question(
            questions,
            mastery_by_concept={"concept-1": 0.2},
            next_review_by_concept={
                "concept-1": datetime(2026, 11, 22, 12, 0),
            },
        )
