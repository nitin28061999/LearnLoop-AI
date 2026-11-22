
from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class QuestionCandidate:
    question_id: str
    concept_id: str
    question_text: str
    difficulty: int


def target_difficulty(mastery: float) -> int:
    # sourcery skip: assign-if-exp, reintroduce-else
    if not isfinite(mastery) or not 0.0 <= mastery <= 1.0:
        raise ValueError("Mastery must be between 0 and 1.")

    if mastery < 0.30:
        return 1
    if mastery < 0.50:
        return 2
    if mastery < 0.70:
        return 3
    if mastery < 0.85:
        return 4
    return 5


def select_adaptive_question(
    questions: list[QuestionCandidate],
    mastery_by_concept: dict[str, float],
    attempted_question_texts: set[str] | None = None,
    prerequisites_by_concept: dict[str, set[str]] | None = None,
) -> QuestionCandidate | None:
    if not questions:
        return None

    attempted = attempted_question_texts or set()
    prerequisites = prerequisites_by_concept or {}

    for concept_id, mastery in mastery_by_concept.items():
        if not isinstance(mastery, (int, float)) or isinstance(mastery, bool):
            raise ValueError(f"Invalid mastery for concept {concept_id}.")

        if not isfinite(mastery) or not 0.0 <= mastery <= 1.0:
            raise ValueError(f"Invalid mastery for concept {concept_id}.")

    for question in questions:
        if not 1 <= question.difficulty <= 5:
            raise ValueError("Question difficulty must be between 1 and 5.")

        if not question.question_id.strip() or not question.concept_id.strip():
            raise ValueError("Question and concept IDs are required.")

        if not question.question_text.strip():
            raise ValueError("Question text must not be empty.")

    eligible_questions = [
        question
        for question in questions
        if all(
            mastery_by_concept.get(prerequisite_id, 0.2) >= 0.70
            for prerequisite_id in prerequisites.get(question.concept_id, set())
        )
    ]

    if not eligible_questions:
        return None

    def selection_score(question: QuestionCandidate) -> tuple:
        mastery = mastery_by_concept.get(question.concept_id, 0.2)
        desired_difficulty = target_difficulty(mastery)

        return (
            mastery,
            abs(question.difficulty - desired_difficulty),
            question.question_text in attempted,
            question.question_id,
        )

    return min(eligible_questions, key=selection_score)
