from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client

from app.ai.evaluator import EvaluationError, GeminiAnswerEvaluator
from app.api.dependencies import (
    get_answer_evaluator,
    get_current_user,
    get_supabase,
)
from app.learning.adaptive_service import AdaptiveQuestionService
from app.learning.service import LearningService
from app.schemas.learning import (
    AdaptiveQuestionResponse,
    LearningAttemptRequest,
    LearningAttemptResponse,
)
from app.services.adaptive_question_repository import (
    AdaptiveQuestionDataError,
    AdaptiveQuestionRepository,
)
from app.services.question_repository import (
    QuestionDataError,
    QuestionRepository,
)

router = APIRouter(prefix="/learning", tags=["Learning"])


@router.post(
    "/attempts",
    response_model=LearningAttemptResponse,
    status_code=status.HTTP_200_OK,
)
def record_learning_attempt(
    payload: LearningAttemptRequest,
    user=Depends(get_current_user),
    client: Client = Depends(get_supabase),
    evaluate_answer: GeminiAnswerEvaluator = Depends(get_answer_evaluator),
) -> LearningAttemptResponse:
    try:
        question = QuestionRepository(client).get_for_evaluation(
            str(payload.question_id)
        )
    except QuestionDataError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Question data is unavailable.",
        ) from exc

    if question is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found.",
        )

    try:
        evaluation = evaluate_answer.evaluate(
            question_text=question.question_text,
            expected_answer=question.expected_answer,
            acceptable_answers=question.acceptable_answers,
            grading_rubric=question.grading_rubric,
            misconception_targets=question.misconception_targets,
            student_answer=payload.student_answer,
            reasoning=payload.reasoning,
        )
    except EvaluationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Answer evaluation is unavailable. Please retry.",
        ) from exc

    is_correct = evaluation.is_correct

    if not isinstance(is_correct, bool):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Answer evaluation returned an invalid result.",
        )

    service = LearningService(client)

    try:
        result = service.record_answer(
            student_id=str(user.id),
            concept_id=question.concept_id,
            question_text=question.question_text,
            student_answer=payload.student_answer,
            reasoning=payload.reasoning,
            is_correct=is_correct,
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Learning progress could not be saved. Please retry.",
        ) from exc

    return LearningAttemptResponse(
        concept_id=UUID(question.concept_id),
        mastery_before=result.mastery_before,
        mastery_after=result.mastery_after,
        is_correct=evaluation.is_correct,
        feedback=evaluation.feedback,
        misconceptions=evaluation.misconceptions,
    )


@router.get(
    "/next-question",
    response_model=AdaptiveQuestionResponse,
    status_code=status.HTTP_200_OK,
)
def get_next_question(
    user=Depends(get_current_user),
    client: Client = Depends(get_supabase),
) -> AdaptiveQuestionResponse:
    repository = AdaptiveQuestionRepository(client)
    service = AdaptiveQuestionService(repository)

    try:
        question = service.get_next_question(str(user.id))
    except AdaptiveQuestionDataError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Adaptive question data is unavailable.",
        ) from exc

    if question is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active questions are available.",
        )

    return AdaptiveQuestionResponse(
        question_id=UUID(question.question_id),
        concept_id=UUID(question.concept_id),
        question_text=question.question_text,
        difficulty=question.difficulty,
    )
