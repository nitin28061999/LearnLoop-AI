
from collections.abc import Sequence
from dataclasses import dataclass, field
from math import isfinite

from supabase import Client

from app.learning.adaptive import QuestionCandidate


class AdaptiveQuestionDataError(Exception):
    """Raised when adaptive question data is invalid."""


@dataclass(frozen=True)
class AdaptiveSelectionContext:
    questions: list[QuestionCandidate]
    mastery_by_concept: dict[str, float]
    attempted_question_texts: set[str]
    prerequisites_by_concept: dict[str, set[str]] = field(default_factory=dict)


class AdaptiveQuestionRepository:
    """Retrieves question candidates and student learning context."""

    def __init__(self, client: Client) -> None:
        self.client = client

    def get_selection_context(
        self,
        student_id: str,
    ) -> AdaptiveSelectionContext:
        if not isinstance(student_id, str) or not student_id.strip():
            raise ValueError("student_id is required.")

        try:
            question_response = (
                self.client.table("questions")
                .select("id, concept_id, question_text, difficulty")
                .eq("is_active", True)
                .execute()
            )

            mastery_response = (
                self.client.table("student_concept_mastery")
                .select("concept_id, mastery_probability")
                .eq("student_id", student_id)
                .execute()
            )

            attempt_response = (
                self.client.table("learning_attempts")
                .select("question_text")
                .eq("student_id", student_id)
                .order("created_at", desc=True)
                .limit(100)
                .execute()
            )

            prerequisite_response = (
                self.client.table("concept_prerequisites")
                .select("concept_id, prerequisite_concept_id")
                .execute()
            )
        except Exception as exc:
            raise AdaptiveQuestionDataError(
                "Could not retrieve adaptive learning data."
            ) from exc

        questions = self._build_questions(question_response.data or [])
        mastery = self._build_mastery(mastery_response.data or [])
        attempted = self._build_attempts(attempt_response.data or [])
        prerequisites = self._build_prerequisites(
            prerequisite_response.data or []
        )

        return AdaptiveSelectionContext(
            questions=questions,
            mastery_by_concept=mastery,
            attempted_question_texts=attempted,
            prerequisites_by_concept=prerequisites,
        )

    @staticmethod
    def _build_questions(
        rows: Sequence[object],
    ) -> list[QuestionCandidate]:
        questions = []

        for row in rows:
            if not isinstance(row, dict):
                raise AdaptiveQuestionDataError(
                    "Invalid question record."
                )

            question_id = row.get("id")
            concept_id = row.get("concept_id")
            question_text = row.get("question_text")
            difficulty = row.get("difficulty")

            if (
                not isinstance(question_id, str)
                or not question_id.strip()
                or not isinstance(concept_id, str)
                or not concept_id.strip()
                or not isinstance(question_text, str)
                or not question_text.strip()
            ):
                raise AdaptiveQuestionDataError(
                    "Question fields are invalid."
                )

            if (
                not isinstance(difficulty, int)
                or isinstance(difficulty, bool)
                or not 1 <= difficulty <= 5
            ):
                raise AdaptiveQuestionDataError(
                    "Question difficulty is invalid."
                )

            questions.append(
                QuestionCandidate(
                    question_id=question_id,
                    concept_id=concept_id,
                    question_text=question_text,
                    difficulty=difficulty,
                )
            )

        return questions

    @staticmethod
    def _build_mastery(
        rows: Sequence[object],
    ) -> dict[str, float]:
        mastery_by_concept = {}

        for row in rows:
            if not isinstance(row, dict):
                raise AdaptiveQuestionDataError(
                    "Invalid mastery record."
                )

            concept_id = row.get("concept_id")
            mastery = row.get("mastery_probability")

            if (
                not isinstance(concept_id, str)
                or not concept_id.strip()
                or not isinstance(mastery, (int, float))
                or isinstance(mastery, bool)
            ):
                raise AdaptiveQuestionDataError(
                    "Mastery fields are invalid."
                )

            mastery = float(mastery)

            if not isfinite(mastery) or not 0.0 <= mastery <= 1.0:
                raise AdaptiveQuestionDataError(
                    "Mastery probability is invalid."
                )

            if concept_id in mastery_by_concept:
                raise AdaptiveQuestionDataError(
                    "Duplicate concept mastery record."
                )

            mastery_by_concept[concept_id] = mastery

        return mastery_by_concept

    @staticmethod
    def _build_attempts(
        rows: Sequence[object],
    ) -> set[str]:
        attempted = set()

        for row in rows:
            if (
                not isinstance(row, dict)
                or not isinstance(row.get("question_text"), str)
                or not row["question_text"].strip()
            ):
                raise AdaptiveQuestionDataError(
                    "Invalid learning attempt record."
                )

            attempted.add(row["question_text"])

        return attempted

    @staticmethod
    def _build_prerequisites(
        rows: Sequence[object],
    ) -> dict[str, set[str]]:
        prerequisites_by_concept: dict[str, set[str]] = {}

        for row in rows:
            if not isinstance(row, dict):
                raise AdaptiveQuestionDataError(
                    "Invalid prerequisite record."
                )

            concept_id = row.get("concept_id")
            prerequisite_concept_id = row.get("prerequisite_concept_id")

            if (
                not isinstance(concept_id, str)
                or not concept_id.strip()
                or not isinstance(prerequisite_concept_id, str)
                or not prerequisite_concept_id.strip()
                or concept_id == prerequisite_concept_id
            ):
                raise AdaptiveQuestionDataError(
                    "Prerequisite fields are invalid."
                )

            concept_prerequisites = prerequisites_by_concept.setdefault(
                concept_id,
                set(),
            )

            if prerequisite_concept_id in concept_prerequisites:
                raise AdaptiveQuestionDataError(
                    "Duplicate concept prerequisite record."
                )

            concept_prerequisites.add(prerequisite_concept_id)

        return prerequisites_by_concept
