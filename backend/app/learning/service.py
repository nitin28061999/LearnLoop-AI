
from dataclasses import dataclass
from datetime import UTC, datetime
from math import isfinite
from typing import cast

from supabase import Client

from app.learning.bkt import BKTParameters, update_mastery
from app.learning.spaced_repetition import ReviewState, schedule_next_review

MAX_CONCURRENCY_RETRIES = 3


@dataclass(frozen=True)
class LearningResult:
    mastery_before: float
    mastery_after: float
    review_state: ReviewState


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
        reviewed_at: datetime | None = None,
    ) -> LearningResult:
        """Calculate mastery and persist the answer with concurrency retries."""

        if not isinstance(is_correct, bool):
            raise ValueError("is_correct must be a boolean.")

        if not student_id.strip() or not concept_id.strip():
            raise ValueError("student_id and concept_id are required.")

        if not question_text.strip() or not student_answer.strip():
            raise ValueError("question_text and student_answer are required.")

        reviewed_at = reviewed_at or datetime.now(UTC)
        if reviewed_at.tzinfo is None or reviewed_at.utcoffset() is None:
            raise ValueError("reviewed_at must be timezone-aware.")

        for _ in range(MAX_CONCURRENCY_RETRIES):
            response = (
                self.client.table("student_concept_mastery")
                .select(
                    "mastery_probability, attempts_count, "
                    "repetition_count, review_interval_days, ease_factor, "
                    "next_review_at, last_reviewed_at"
                )
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

            row = cast(dict[str, object], rows[0]) if rows else {}
            repetition_count_raw = cast(
                int | float | str,
                row.get("repetition_count", 0),
            )
            interval_raw = cast(
                int | float | str,
                row.get("review_interval_days", 0),
            )
            ease_factor_raw = cast(
                int | float | str,
                row.get("ease_factor", 2.5),
            )
            previous_review_state = ReviewState(
                repetition_count=int(repetition_count_raw),
                interval_days=int(interval_raw),
                ease_factor=float(ease_factor_raw),
            )
            review_state = schedule_next_review(
                state=previous_review_state,
                is_correct=is_correct,
                reviewed_at=reviewed_at,
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
                    "p_repetition_count": review_state.repetition_count,
                    "p_review_interval_days": review_state.interval_days,
                    "p_ease_factor": review_state.ease_factor,
                    "p_next_review_at": (
                        review_state.next_review_at.isoformat()
                        if review_state.next_review_at is not None
                        else None
                    ),
                    "p_last_reviewed_at": (
                        review_state.last_reviewed_at.isoformat()
                        if review_state.last_reviewed_at is not None
                        else None
                    ),
                },
            ).execute()

            result = rpc_response.data

            if isinstance(result, dict) and result.get("success") is True:
                return LearningResult(
                    mastery_before=mastery_before,
                    mastery_after=mastery_after,
                    review_state=review_state,
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
