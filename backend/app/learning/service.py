
from dataclasses import dataclass
from math import isfinite

from supabase import Client

from app.learning.bkt import BKTParameters, update_mastery

MAX_CONCURRENCY_RETRIES = 3


@dataclass(frozen=True)
class LearningResult:
    mastery_before: float
    mastery_after: float


class LearningService:
    """Coordinates BKT mastery updates and atomic persistence."""

    def __init__(
        self,
        client: Client,
        parameters: BKTParameters | None = None,
    ) -> None:
        self.client = client
        self.parameters = parameters or BKTParameters()

    def record_answer(
        self,
        student_id: str,
        concept_id: str,
        question_text: str,
        student_answer: str,
        reasoning: str | None,
        is_correct: bool,
    ) -> LearningResult:
        """Calculate mastery and persist the answer with concurrency retries."""

        if not isinstance(is_correct, bool):
            raise ValueError("is_correct must be a boolean.")

        if not student_id.strip() or not concept_id.strip():
            raise ValueError("student_id and concept_id are required.")

        if not question_text.strip() or not student_answer.strip():
            raise ValueError("question_text and student_answer are required.")

        for _ in range(MAX_CONCURRENCY_RETRIES):
            response = (
                self.client.table("student_concept_mastery")
                .select("mastery_probability, attempts_count")
                .eq("student_id", student_id)
                .eq("concept_id", concept_id)
                .limit(1)
                .execute()
            )

            rows = response.data or []

            mastery_before = (
                float(rows[0]["mastery_probability"]) # type: ignore
                if rows
                else self.parameters.p_initial
            )
            expected_attempts_count = (
                int(rows[0]["attempts_count"]) # type: ignore
                if rows
                else 0
            )

            if not isfinite(mastery_before):
                raise ValueError("Stored mastery must be finite.")

            mastery_after = update_mastery(
                prior_mastery=mastery_before,
                is_correct=is_correct,
                parameters=self.parameters,
            )

            rpc_response = self.client.rpc(
                "record_learning_attempt",
                {
                    "p_student_id": student_id,
                    "p_concept_id": concept_id,
                    "p_question_text": question_text,
                    "p_student_answer": student_answer,
                    "p_reasoning": reasoning,
                    "p_is_correct": is_correct,
                    "p_mastery_before": mastery_before,
                    "p_mastery_after": mastery_after,
                    "p_expected_attempts_count": expected_attempts_count,
                },
            ).execute()

            result = rpc_response.data

            if isinstance(result, dict) and result.get("success") is True:
                return LearningResult(
                    mastery_before=mastery_before,
                    mastery_after=mastery_after,
                )

            if (
                isinstance(result, dict)
                and result.get("reason") == "stale_attempt_count"
            ):
                continue

            raise RuntimeError(
                "Could not record learning attempt: "
                f"{result!r}"
            )

        raise RuntimeError(
            "Could not record learning attempt after "
            f"{MAX_CONCURRENCY_RETRIES} concurrency retries."
        )
