from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.evaluation import MisconceptionFinding


class LearningAttemptRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    question_id: UUID
    student_answer: str = Field(min_length=1, max_length=5000)
    reasoning: str = Field(min_length=1, max_length=10000)


class LearningAttemptResponse(BaseModel):
    concept_id: UUID
    mastery_before: float = Field(ge=0.0, le=1.0)
    mastery_after: float = Field(ge=0.0, le=1.0)
    is_correct: bool
    feedback: str = Field(min_length=1, max_length=2000)
    misconceptions: list[MisconceptionFinding] = Field(max_length=10)


class AdaptiveQuestionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_id: UUID
    concept_id: UUID
    question_text: str = Field(min_length=1)
    difficulty: int = Field(ge=1, le=5)
