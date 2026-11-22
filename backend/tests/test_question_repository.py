
from unittest.mock import MagicMock

import pytest  # pyright: ignore[reportMissingImports]

from app.services.question_repository import (  # pyright: ignore[reportMissingImports]
    QuestionDataError,
    QuestionRepository,
)


@pytest.fixture
def mock_supabase():
    client = MagicMock()

    question_query = MagicMock()
    answer_key_query = MagicMock()

    client.table.side_effect = [
        question_query,
        answer_key_query,
    ]

    for query in (question_query, answer_key_query):
        query.select.return_value = query
        query.eq.return_value = query
        query.limit.return_value = query

    return client, question_query, answer_key_query


def test_get_for_evaluation_returns_trusted_question(mock_supabase):
    client, question_query, answer_key_query = mock_supabase

    question_query.execute.return_value.data = [
        {
            "id": "question-123",
            "concept_id": "concept-456",
            "question_text": "What is reflection?",
        }
    ]

    answer_key_query.execute.return_value.data = [
        {
            "expected_answer": "Light returns into the same medium.",
            "acceptable_answers": ["Light bounces back."],
            "grading_rubric": "Explain the return of light.",
            "misconception_targets": [
                {
                    "code": "REFLECTION_DIRECTION",
                    "description": "Confuses reflection with refraction.",
                }
            ],
        }
    ]

    repository = QuestionRepository(client)
    result = repository.get_for_evaluation("question-123")

    assert result is not None
    assert result.question_id == "question-123"
    assert result.concept_id == "concept-456"
    assert result.question_text == "What is reflection?"
    assert result.expected_answer == "Light returns into the same medium."
    assert result.acceptable_answers == ["Light bounces back."]
    assert result.grading_rubric == "Explain the return of light."
    assert result.misconception_targets[0]["code"] == "REFLECTION_DIRECTION"


def test_get_for_evaluation_returns_none_for_unknown_question(mock_supabase):
    client, question_query, _ = mock_supabase
    question_query.execute.return_value.data = []

    repository = QuestionRepository(client)

    assert repository.get_for_evaluation("unknown-question") is None
    assert client.table.call_count == 1


def test_get_for_evaluation_rejects_missing_answer_key(mock_supabase):
    client, question_query, answer_key_query = mock_supabase

    question_query.execute.return_value.data = [
        {
            "id": "question-123",
            "concept_id": "concept-456",
            "question_text": "What is reflection?",
        }
    ]

    answer_key_query.execute.return_value.data = []

    repository = QuestionRepository(client)

    with pytest.raises(QuestionDataError):
        repository.get_for_evaluation("question-123")

def test_get_for_evaluation_rejects_empty_expected_answer(mock_supabase):
    client, question_query, answer_key_query = mock_supabase

    question_query.execute.return_value.data = [
        {
            "id": "question-123",
            "concept_id": "concept-456",
            "question_text": "What is reflection?",
        }
    ]

    answer_key_query.execute.return_value.data = [
        {
            "expected_answer": " ",
            "acceptable_answers": [],
            "grading_rubric": "Explain reflection.",
            "misconception_targets": [],
        }
    ]

    repository = QuestionRepository(client)

    with pytest.raises(QuestionDataError):
        repository.get_for_evaluation("question-123")


@pytest.mark.parametrize("question_text", ["", "   ", None, 42])
def test_get_for_evaluation_rejects_invalid_question_text(
    mock_supabase,
    question_text,
):
    client, question_query, answer_key_query = mock_supabase

    question_query.execute.return_value.data = [
        {
            "id": "question-123",
            "concept_id": "concept-456",
            "question_text": question_text,
        }
    ]

    answer_key_query.execute.return_value.data = [
        {
            "expected_answer": "Light returns into the same medium.",
            "acceptable_answers": [],
            "grading_rubric": "Explain reflection.",
            "misconception_targets": [],
        }
    ]

    repository = QuestionRepository(client)

    with pytest.raises(QuestionDataError, match="Question text must not be empty"):
        repository.get_for_evaluation("question-123")


def test_get_for_evaluation_rejects_invalid_misconception_targets(
    mock_supabase,
):
    client, question_query, answer_key_query = mock_supabase

    question_query.execute.return_value.data = [
        {
            "id": "question-123",
            "concept_id": "concept-456",
            "question_text": "What is reflection?",
        }
    ]

    answer_key_query.execute.return_value.data = [
        {
            "expected_answer": "Light returns into the same medium.",
            "acceptable_answers": [],
            "grading_rubric": "Explain reflection.",
            "misconception_targets": "not-a-list",
        }
    ]

    repository = QuestionRepository(client)

    with pytest.raises(QuestionDataError):
        repository.get_for_evaluation("question-123")
