
from unittest.mock import MagicMock

from app.learning.adaptive import QuestionCandidate
from app.learning.adaptive_service import AdaptiveQuestionService  # pyright: ignore[reportMissingImports]
from app.services.adaptive_question_repository import (
    AdaptiveSelectionContext,
)


def test_service_returns_adaptive_question():
    repository = MagicMock()

    repository.get_selection_context.return_value = AdaptiveSelectionContext(
        questions=[
            QuestionCandidate("q1", "strong", "Question 1", 3),
            QuestionCandidate("q2", "weak", "Question 2", 1),
        ],
        mastery_by_concept={
            "strong": 0.8,
            "weak": 0.2,
        },
        attempted_question_texts=set(),
    )

    service = AdaptiveQuestionService(repository)

    result = service.get_next_question("student-123")

    assert result is not None
    assert result.question_id == "q2"

    repository.get_selection_context.assert_called_once_with(
        "student-123"
    )


def test_service_returns_none_when_no_questions_are_available():
    repository = MagicMock()

    repository.get_selection_context.return_value = AdaptiveSelectionContext(
        questions=[],
        mastery_by_concept={},
        attempted_question_texts=set(),
    )

    service = AdaptiveQuestionService(repository)

    result = service.get_next_question("student-123")

    assert result is None


def test_service_rejects_empty_student_id():
    repository = MagicMock()
    service = AdaptiveQuestionService(repository)

    try:
        service.get_next_question(" ")
    except ValueError as exc:
        assert "student_id" in str(exc)
    else:
        raise AssertionError("Expected ValueError.")

    repository.get_selection_context.assert_not_called()


def test_service_blocks_question_when_prerequisite_mastery_is_low():
    repository = MagicMock()

    repository.get_selection_context.return_value = AdaptiveSelectionContext(
        questions=[
            QuestionCandidate(
                "q-dependent",
                "dependent",
                "Question requiring prerequisite",
                2,
            ),
            QuestionCandidate(
                "q-root",
                "root",
                "Root concept question",
                1,
            ),
        ],
        mastery_by_concept={
            "dependent": 0.2,
            "root": 0.2,
            "prerequisite": 0.5,
        },
        attempted_question_texts=set(),
        prerequisites_by_concept={
            "dependent": {"prerequisite"},
        },
    )

    service = AdaptiveQuestionService(repository)

    result = service.get_next_question("student-123")

    assert result is not None
    assert result.question_id == "q-root"
