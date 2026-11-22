
from pydantic import BaseModel, ConfigDict, Field


class MisconceptionFinding(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    code: str = Field(min_length=1, max_length=100)
    evidence: str = Field(min_length=1, max_length=1000)
    explanation: str = Field(min_length=1, max_length=1000)


class AnswerEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    is_correct: bool
    misconceptions: list[MisconceptionFinding] = Field(max_length=10)
    feedback: str = Field(min_length=1, max_length=2000)
