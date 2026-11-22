
from unittest.mock import MagicMock

import pytest  # pyright: ignore[reportMissingImports]

from app.ai.evaluator import (  # pyright: ignore[reportMissingImports]
    EvaluationError,
    GeminiAnswerEvaluator,
)


@pytest.fixture
def misconception_targets():
    return [
        {
            "code": "REFLECTION_DIRECTION",
            "description": "Confuses reflection with refraction.",
        },
        {
            "code": "NORMAL_RAY_CONFUSION",
            "description": "Confuses the normal with a light ray.",
        },
    ]


@pytest.fixture
def valid_model_response():
    return {
        "is_correct": False,
        "misconceptions": [
            {
                "code": "REFLECTION_DIRECTION",
                "evidence": "The student says light bends into another medium.",
                "explanation": "This describes refraction, not reflection.",
            }
        ],
        "feedback": "Review how reflection differs from refraction.",
    }


def build_evaluator(response):
    client = MagicMock()
    client.models.generate_content.return_value = MagicMock(
        parsed=response,
        text=None,
    )

    return GeminiAnswerEvaluator(
        client=client,
        model="gemini-2.5-flash",
    ), client


def test_evaluator_returns_structured_evaluation(
    misconception_targets,
    valid_model_response,
):
    evaluator, client = build_evaluator(valid_model_response)

    result = evaluator.evaluate(
        question_text="What is reflection?",
        expected_answer="Light returns into the same medium.",
        acceptable_answers=[],
        grading_rubric="Explain the return of light into its original medium.",
        misconception_targets=misconception_targets,
        student_answer="Light bends into another medium.",
        reasoning="It changes direction when it hits a surface.",
    )

    assert result.is_correct is False
    assert result.misconceptions[0].code == "REFLECTION_DIRECTION"
    client.models.generate_content.assert_called_once()


def test_evaluator_rejects_unknown_misconception_code(
    misconception_targets,
    valid_model_response,
):
    valid_model_response["misconceptions"][0]["code"] = "INVENTED_CODE"
    evaluator, _ = build_evaluator(valid_model_response)

    with pytest.raises(EvaluationError):
        evaluator.evaluate(
            question_text="What is reflection?",
            expected_answer="Light returns into the same medium.",
            acceptable_answers=[],
            grading_rubric="Explain reflection.",
            misconception_targets=misconception_targets,
            student_answer="Light bends.",
            reasoning=None,
        )


def test_evaluator_rejects_malformed_model_response(
    misconception_targets,
):
    evaluator, _ = build_evaluator(
        {"is_correct": "probably", "misconceptions": [], "feedback": ""}
    )

    with pytest.raises(EvaluationError):
        evaluator.evaluate(
            question_text="What is reflection?",
            expected_answer="Light returns into the same medium.",
            acceptable_answers=[],
            grading_rubric="Explain reflection.",
            misconception_targets=misconception_targets,
            student_answer="Light returns.",
            reasoning=None,
        )


def test_evaluator_rejects_missing_model_response(
    misconception_targets,
):
    evaluator, _ = build_evaluator(None)

    with pytest.raises(EvaluationError):
        evaluator.evaluate(
            question_text="What is reflection?",
            expected_answer="Light returns into the same medium.",
            acceptable_answers=[],
            grading_rubric="Explain reflection.",
            misconception_targets=misconception_targets,
            student_answer="Light returns.",
            reasoning=None,
        )


def test_evaluator_sends_structured_output_configuration(
    misconception_targets,
    valid_model_response,
):
    evaluator, client = build_evaluator(valid_model_response)

    evaluator.evaluate(
        question_text="What is reflection?",
        expected_answer="Light returns into the same medium.",
        acceptable_answers=[],
        grading_rubric="Explain reflection.",
        misconception_targets=misconception_targets,
        student_answer="Light returns.",
        reasoning=None,
    )

    _, kwargs = client.models.generate_content.call_args
    assert kwargs["model"] == "gemini-2.5-flash"
    assert kwargs["config"].response_mime_type == "application/json"
