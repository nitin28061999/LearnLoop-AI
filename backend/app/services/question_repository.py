
from dataclasses import dataclass
from typing import Any

from supabase import Client


class QuestionDataError(Exception):
    """Raised when trusted question data is incomplete or invalid."""


def _validate_answer_key(answer_key: dict[str, Any]) -> None:
    if not isinstance(answer_key, dict):
        raise QuestionDataError("Invalid answer key.")

    expected_answer = answer_key.get("expected_answer")
    grading_rubric = answer_key.get("grading_rubric")
    acceptable_answers = answer_key.get("acceptable_answers")
    misconception_targets = answer_key.get("misconception_targets")

    if not isinstance(expected_answer, str) or not expected_answer.strip():
        raise QuestionDataError("Expected answer must not be empty.")

    if not isinstance(grading_rubric, str) or not grading_rubric.strip():
        raise QuestionDataError("Grading rubric must not be empty.")

    if (
        not isinstance(acceptable_answers, list)
        or not all(
            isinstance(answer, str) and answer.strip()
            for answer in acceptable_answers
        )
    ):
        raise QuestionDataError("Acceptable answers must be a list of strings.")

    if not isinstance(misconception_targets, list):
        raise QuestionDataError("Misconception targets must be a list.")

    codes: set[str] = set()

    for target in misconception_targets:
        if not isinstance(target, dict):
            raise QuestionDataError("Invalid misconception target.")

        code = target.get("code")
        description = target.get("description")

        if (
            not isinstance(code, str)
            or not code.strip()
            or not isinstance(description, str)
            or not description.strip()
            or code in codes
        ):
            raise QuestionDataError("Invalid misconception target.")

        codes.add(code)


@dataclass(frozen=True)
class QuestionForEvaluation:
    question_id: str
    concept_id: str
    question_text: str
    expected_answer: str
    acceptable_answers: list[str]
    grading_rubric: str
    misconception_targets: list[dict[str, Any]]


class QuestionRepository:
    """Retrieves trusted questions and answer keys from Supabase."""

    def __init__(self, client: Client) -> None:
        self.client = client

    def get_for_evaluation(
        self,
        question_id: str,
    ) -> QuestionForEvaluation | None:
        question_response = (
            self.client.table("questions")
            .select("id, concept_id, question_text")
            .eq("id", question_id)
            .eq("is_active", True)
            .limit(1)
            .execute()
        )

        questions = question_response.data or []

        if not questions:
            return None

        question = questions[0]

        if not isinstance(question, dict):
            raise QuestionDataError(
                "The question or answer key contains invalid data."
            )

        answer_key_response = (
            self.client.table("question_answer_keys")
            .select(
                "expected_answer, acceptable_answers, "
                "grading_rubric, misconception_targets"
            )
            .eq("question_id", question_id)
            .limit(1)
            .execute()
        )

        answer_keys = answer_key_response.data or []

        if not answer_keys:
            raise QuestionDataError(
                "The question does not have a configured answer key."
            )

        answer_key = answer_keys[0]
        _validate_answer_key(answer_key) # pyright: ignore[reportArgumentType]

        misconception_targets = answer_key["misconception_targets"] # pyright: ignore[reportIndexIssue, reportCallIssue, reportArgumentType, reportOptionalSubscript]
        if not isinstance(misconception_targets, list) or not all(
            isinstance(target, dict) for target in misconception_targets
        ):
            raise QuestionDataError(
                "The question or answer key contains invalid data."
            )

        try:
            if (
                not isinstance(question["question_text"], str)
                or not question["question_text"].strip()
            ):
                raise QuestionDataError("Question text must not be empty.")

            return QuestionForEvaluation(
                question_id=str(question["id"]),
                concept_id=str(question["concept_id"]),
                question_text=question["question_text"], # pyright: ignore[reportArgumentType] # pyright: ignore[reportCallIssue] # pyright: ignore[reportOptionalSubscript]
                expected_answer=answer_key["expected_answer"], # pyright: ignore[reportArgumentType] # pyright: ignore[reportIndexIssue] # pyright: ignore[reportOptionalSubscript] # pyright: ignore[reportCallIssue] # pyright: ignore[reportIndexIssue] # type: ignore
                acceptable_answers=answer_key["acceptable_answers"], # pyright: ignore[reportArgumentType] # type: ignore
                grading_rubric=answer_key["grading_rubric"], # pyright: ignore[reportArgumentType] # type: ignore
                misconception_targets=misconception_targets, # pyright: ignore[reportArgumentType]
            )
        except (KeyError, TypeError) as exc:
            raise QuestionDataError(
                "The question or answer key contains invalid data."
            ) from exc
