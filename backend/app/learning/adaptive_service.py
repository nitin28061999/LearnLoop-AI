
from app.learning.adaptive import (
    QuestionCandidate,
    select_adaptive_question,
)
from app.services.adaptive_question_repository import (
    AdaptiveQuestionRepository,
)


class AdaptiveQuestionService:
    """Coordinates adaptive question retrieval and selection."""

    def __init__(self, repository: AdaptiveQuestionRepository) -> None:
        self.repository = repository

    def get_next_question(
        self,
        student_id: str,
    ) -> QuestionCandidate | None:
        if not isinstance(student_id, str) or not student_id.strip():
            raise ValueError("student_id is required.")

        context = self.repository.get_selection_context(student_id)

        return select_adaptive_question(
            questions=context.questions,
            mastery_by_concept=context.mastery_by_concept,
            attempted_question_texts=context.attempted_question_texts,
            prerequisites_by_concept=context.prerequisites_by_concept,
        )
