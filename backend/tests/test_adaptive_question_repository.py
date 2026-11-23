
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest  # pyright: ignore[reportMissingImports]

from app.services.adaptive_question_repository import (  # pyright: ignore[reportMissingImports]
    AdaptiveQuestionDataError,
    AdaptiveQuestionRepository,
)


def build_mock_client():
    client = MagicMock() # pyright: ignore[reportGeneralTypeIssues]

    question_query = MagicMock()
    mastery_query = MagicMock()
    attempt_query = MagicMock()
    prerequisite_query = MagicMock()

    client.table.side_effect = [
        question_query,
        mastery_query,
        attempt_query,
        prerequisite_query,
    ]

    for query in (
        question_query,
        mastery_query,
        attempt_query,
        prerequisite_query,
    ):
        query.select.return_value = query
        query.eq.return_value = query
        query.order.return_value = query
        query.limit.return_value = query

    question_query.execute.return_value = SimpleNamespace(
        data=[
            {
                "id": "q1",
                "concept_id": "concept-1",
                "question_text": "What is reflection?",
                "difficulty": 1,
            },
            {
                "id": "q2",
                "concept_id": "concept-2",
                "question_text": "Define resistance.",
                "difficulty": 3,
            },
        ]
    )

    mastery_query.execute.return_value = SimpleNamespace(
        data=[
            {
                "concept_id": "concept-1",
                "mastery_probability": 0.25,
            },
            {
                "concept_id": "concept-2",
                "mastery_probability": 0.75,
            },
        ]
    )

    attempt_query.execute.return_value = SimpleNamespace(
        data=[
            {"question_text": "What is reflection?"},
        ]
    )
    prerequisite_query.execute.return_value = SimpleNamespace(
        data=[
            {
                "concept_id": "concept-2",
                "prerequisite_concept_id": "concept-1",
            },
            {
                "concept_id": "concept-3",
                "prerequisite_concept_id": "concept-2",
            },
        ]
    )

    return (
        client,
        question_query,
        mastery_query,
        attempt_query,
        prerequisite_query,
    )


def test_repository_returns_question_candidates_and_student_context():
    (
        client,
        _question_query,
        mastery_query,
        attempt_query,
        _prerequisite_query,
    ) = build_mock_client()

    repository = AdaptiveQuestionRepository(client)
    context = repository.get_selection_context("student-123")

    assert len(context.questions) == 2
    assert context.questions[0].question_id == "q1"
    assert context.questions[0].difficulty == 1

    assert context.mastery_by_concept == {
        "concept-1": 0.25,
        "concept-2": 0.75,
    }

    assert context.attempted_question_texts == {
        "What is reflection?"
    }

    assert client.table.call_args_list[0].args[0] == "questions"
    assert client.table.call_args_list[1].args[0] == (
        "student_concept_mastery"
    )
    assert client.table.call_args_list[2].args[0] == (
        "learning_attempts"
    )

    mastery_query.eq.assert_called_once_with(
        "student_id",
        "student-123",
    )
    attempt_query.eq.assert_called_once_with(
        "student_id",
        "student-123",
    )
    attempt_query.order.assert_called_once_with(
        "created_at",
        desc=True,
    )
    attempt_query.limit.assert_called_once_with(100)


def test_repository_handles_student_with_no_learning_history():
    client, _, mastery_query, attempt_query, _ = build_mock_client()

    mastery_query.execute.return_value = SimpleNamespace(data=[])
    attempt_query.execute.return_value = SimpleNamespace(data=[])

    repository = AdaptiveQuestionRepository(client)
    context = repository.get_selection_context("new-student")

    assert context.mastery_by_concept == {}
    assert context.attempted_question_texts == set()
    assert len(context.questions) == 2


@pytest.mark.parametrize(
    "invalid_question",
    [
        {
            "id": "",
            "concept_id": "c1",
            "question_text": "Question",
            "difficulty": 1,
        },
        {
            "id": "q1",
            "concept_id": "",
            "question_text": "Question",
            "difficulty": 1,
        },
        {
            "id": "q1",
            "concept_id": "c1",
            "question_text": " ",
            "difficulty": 1,
        },
        {
            "id": "q1",
            "concept_id": "c1",
            "question_text": "Question",
            "difficulty": 6,
        },
        {
            "id": "q1",
            "concept_id": "c1",
            "question_text": "Question",
            "difficulty": True,
        },
    ],
)
def test_repository_rejects_invalid_question_records(invalid_question):
    with pytest.raises(AdaptiveQuestionDataError):
        AdaptiveQuestionRepository._build_questions([invalid_question])


@pytest.mark.parametrize(
    "invalid_mastery",
    [
        {"concept_id": "c1", "mastery_probability": 1.5},
        {"concept_id": "c1", "mastery_probability": -0.1},
        {"concept_id": "c1", "mastery_probability": float("nan")},
        {"concept_id": "", "mastery_probability": 0.5},
        {"concept_id": "c1", "mastery_probability": True},
    ],
)
def test_repository_rejects_invalid_mastery_records(invalid_mastery):
    with pytest.raises(AdaptiveQuestionDataError):
        AdaptiveQuestionRepository._build_mastery([invalid_mastery])


def test_repository_rejects_invalid_attempt_records():
    with pytest.raises(AdaptiveQuestionDataError):
        AdaptiveQuestionRepository._build_attempts(
            [{"question_text": "  "}]
        )


def test_repository_rejects_duplicate_mastery_records():
    rows = [
        {"concept_id": "c1", "mastery_probability": 0.3},
        {"concept_id": "c1", "mastery_probability": 0.7},
    ]

    with pytest.raises(AdaptiveQuestionDataError, match="Duplicate"):
        AdaptiveQuestionRepository._build_mastery(rows)


def test_repository_returns_prerequisite_relationships():
    (
        client,
        _question_query,
        _mastery_query,
        _attempt_query,
        _prerequisite_query,
    ) = build_mock_client()

    context = AdaptiveQuestionRepository(
        client
    ).get_selection_context("student-123")

    assert context.prerequisites_by_concept == {
        "concept-2": {"concept-1"},
        "concept-3": {"concept-2"},
    }


def test_repository_rejects_invalid_prerequisite_records():
    invalid_rows = [
        {"concept_id": "", "prerequisite_concept_id": "c1"},
        {"concept_id": "c1", "prerequisite_concept_id": ""},
        {"concept_id": "c1", "prerequisite_concept_id": "c1"},
        {"concept_id": None, "prerequisite_concept_id": "c1"},
        {"concept_id": "c1", "prerequisite_concept_id": None},
        "invalid-record",
    ]

    for row in invalid_rows:
        with pytest.raises(AdaptiveQuestionDataError):
            AdaptiveQuestionRepository._build_prerequisites([row])


def test_repository_rejects_duplicate_prerequisite_relationships():
    rows = [
        {
            "concept_id": "c2",
            "prerequisite_concept_id": "c1",
        },
        {
            "concept_id": "c2",
            "prerequisite_concept_id": "c1",
        },
    ]

    with pytest.raises(AdaptiveQuestionDataError, match="Duplicate"):
        AdaptiveQuestionRepository._build_prerequisites(rows)


def test_repository_returns_next_review_dates_for_student_concepts():
    (
        client,
        _question_query,
        mastery_query,
        _attempt_query,
        _prerequisite_query,
    ) = build_mock_client()

    mastery_query.execute.return_value = SimpleNamespace(
        data=[
            {
                "concept_id": "concept-1",
                "mastery_probability": 0.25,
                "next_review_at": "2026-11-21T12:00:00+00:00",
            },
            {
                "concept_id": "concept-2",
                "mastery_probability": 0.75,
                "next_review_at": None,
            },
        ]
    )

    context = AdaptiveQuestionRepository(
        client
    ).get_selection_context("student-123")

    assert context.next_review_by_concept == {
        "concept-1": datetime(2026, 11, 21, 12, 0, tzinfo=UTC),
    }

    mastery_query.select.assert_called_once_with(
        "concept_id, mastery_probability, next_review_at"
    )
