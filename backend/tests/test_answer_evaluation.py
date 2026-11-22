
import pytest  # pyright: ignore[reportMissingImports]
from pydantic import ValidationError

from app.schemas.evaluation import AnswerEvaluation, MisconceptionFinding  # pyright: ignore[reportMissingImports]


def test_valid_evaluation_with_misconception():
    evaluation = AnswerEvaluation(
        is_correct=False,
        misconceptions=[
            MisconceptionFinding(
                code="REFLECTION_DIRECTION",
                evidence="The student says light bends back into the same medium.",
                explanation=(
                    "Reflection changes the direction of light without changing "
                    "its medium."
                ),
            )
        ],
        feedback="Review the difference between reflection and refraction.",
    )

    assert evaluation.is_correct is False
    assert len(evaluation.misconceptions) == 1
    assert evaluation.misconceptions[0].code == "REFLECTION_DIRECTION"


def test_valid_evaluation_without_misconceptions():
    evaluation = AnswerEvaluation(
        is_correct=True,
        misconceptions=[],
        feedback="Correct. Light returns into the original medium after reflection.",
    )

    assert evaluation.is_correct is True
    assert evaluation.misconceptions == []


def test_evaluation_rejects_empty_feedback():
    with pytest.raises(ValidationError):
        AnswerEvaluation(
            is_correct=True,
            misconceptions=[],
            feedback="   ",
        )


def test_misconception_requires_evidence():
    with pytest.raises(ValidationError):
        MisconceptionFinding(
            code="REFLECTION_DIRECTION",
            evidence="",
            explanation="The student confuses reflection with refraction.",
        )


def test_evaluation_rejects_unexpected_fields():
    with pytest.raises(ValidationError):
        AnswerEvaluation(
            is_correct=True,
            misconceptions=[],
            feedback="Good work.",
            mastery_probability=0.99, # pyright: ignore[reportCallIssue]
        )
