from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest  # pyright: ignore[reportMissingImports]
from fastapi.testclient import TestClient  # pyright: ignore[reportMissingImports]

from app.api.dependencies import (
    get_answer_evaluator,  # pyright: ignore[reportAttributeAccessIssue]
    get_current_user,
    get_supabase,
)
from app.main import app
from app.schemas.evaluation import AnswerEvaluation, MisconceptionFinding


@pytest.fixture
def api_client():
    app.dependency_overrides.clear()
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def mock_supabase():
    client = MagicMock()

    question_query = MagicMock()
    answer_key_query = MagicMock()
    mastery_query = MagicMock()

    client.table.side_effect = [
        question_query,
        answer_key_query,
        mastery_query,
    ]
    client.question_query = question_query

    for query in (question_query, answer_key_query, mastery_query):
        query.select.return_value = query
        query.eq.return_value = query
        query.limit.return_value = query

    question_query.execute.return_value = SimpleNamespace(
        data=[
            {
                "id": "22222222-2222-4222-8222-222222222222",
                "concept_id": "11111111-1111-4111-8111-111111111111",
                "question_text": "What is reflection of light?",
            }
        ]
    )
    answer_key_query.execute.return_value = SimpleNamespace(
        data=[
            {
                "expected_answer": "Light returns to the same medium.",
                "acceptable_answers": ["Light bounces back."],
                "grading_rubric": "Explain the return of light.",
                "misconception_targets": [
                    {
                        "code": "REFLECTION_DIRECTION",
                        "description": "Confuses reflection with refraction.",
                    }
                ],
            }
        ]
    )
    mastery_query.execute.return_value = SimpleNamespace(data=[])

    client.rpc.return_value.execute.return_value = SimpleNamespace(
        data={"success": True}
    )

    app.dependency_overrides[get_supabase] = lambda: client
    return client


@pytest.fixture
def authenticated_client(mock_supabase):
    user = SimpleNamespace(id="authenticated-student-123")
    app.dependency_overrides[get_current_user] = lambda: user
    evaluator = MagicMock()
    evaluator.evaluate.return_value = AnswerEvaluation(
        is_correct=True,
        misconceptions=[
            MisconceptionFinding(
                code="REFLECTION_DIRECTION",
                evidence="The student describes light returning from a surface.",
                explanation="Review the direction of reflected light.",
            )
        ],
        feedback="Good explanation. Keep practising reflection.",
    )
    app.dependency_overrides[get_answer_evaluator] = (
        lambda: evaluator
    )
    mock_supabase.evaluator = evaluator
    return mock_supabase


def valid_payload():
    return {
        "question_id": "22222222-2222-4222-8222-222222222222",
        "student_answer": "Light bounces back from a surface.",
        "reasoning": "The light ray returns after striking the surface.",
    }


def test_learning_attempt_requires_authentication(api_client, mock_supabase):
    response = api_client.post(
        "/api/v1/learning/attempts",
        json=valid_payload(),
    )

    assert response.status_code == 401
    mock_supabase.auth.get_user.assert_not_called()


def test_authenticated_student_can_record_learning_attempt(
    api_client,
    authenticated_client,
):
    response = api_client.post(
        "/api/v1/learning/attempts",
        json=valid_payload(),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["mastery_before"] == pytest.approx(0.2)
    assert body["mastery_after"] == pytest.approx(0.5764705882)
    assert body["is_correct"] is True
    assert body["feedback"] == (
        "Good explanation. Keep practising reflection."
    )
    assert body["misconceptions"] == [
        {
            "code": "REFLECTION_DIRECTION",
            "evidence": (
                "The student describes light returning from a surface."
            ),
            "explanation": "Review the direction of reflected light.",
        }
    ]

    authenticated_client.rpc.assert_called_once()
    function_name, parameters = authenticated_client.rpc.call_args.args

    assert function_name == "record_learning_attempt"
    assert parameters["p_student_id"] == "authenticated-student-123"
    assert parameters["p_concept_id"] == "11111111-1111-4111-8111-111111111111"
    assert parameters["p_question_text"] == "What is reflection of light?"
    assert parameters["p_is_correct"] is True

    authenticated_client.evaluator.evaluate.assert_called_once_with(
        question_text="What is reflection of light?",
        expected_answer="Light returns to the same medium.",
        acceptable_answers=["Light bounces back."],
        grading_rubric="Explain the return of light.",
        misconception_targets=[
            {
                "code": "REFLECTION_DIRECTION",
                "description": "Confuses reflection with refraction.",
            }
        ],
        student_answer="Light bounces back from a surface.",
        reasoning="The light ray returns after striking the surface.",
    )


def test_incorrect_answer_returns_feedback_and_updates_mastery(
    api_client,
    authenticated_client,
):
    authenticated_client.evaluator.evaluate.return_value = AnswerEvaluation(
        is_correct=False,
        misconceptions=[
            MisconceptionFinding(
                code="REFLECTION_DIRECTION",
                evidence="The student confuses reflection and refraction.",
                explanation="These are different phenomena.",
            )
        ],
        feedback="Review the difference between reflection and refraction.",
    )

    response = api_client.post(
        "/api/v1/learning/attempts",
        json=valid_payload(),
    )

    assert response.status_code == 200
    body = response.json()

    assert body["is_correct"] is False
    assert body["mastery_before"] == pytest.approx(0.2)
    assert body["mastery_after"] == pytest.approx(0.1272727273)
    assert body["feedback"] == (
        "Review the difference between reflection and refraction."
    )
    assert body["misconceptions"][0]["code"] == "REFLECTION_DIRECTION"

    _, parameters = authenticated_client.rpc.call_args.args
    assert parameters["p_is_correct"] is False


def test_client_cannot_supply_student_id(
    api_client,
    authenticated_client,
):
    payload = valid_payload()
    payload["student_id"] = "another-student-456"

    response = api_client.post(
        "/api/v1/learning/attempts",
        json=payload,
    )

    assert response.status_code == 422
    authenticated_client.rpc.assert_not_called()


def test_client_cannot_supply_is_correct(
    api_client,
    authenticated_client,
):
    payload = valid_payload()
    payload["is_correct"] = True  # pyright: ignore[reportArgumentType]

    response = api_client.post(
        "/api/v1/learning/attempts",
        json=payload,
    )

    assert response.status_code == 422
    authenticated_client.rpc.assert_not_called()


def test_invalid_question_id_is_rejected(
    api_client,
    authenticated_client,
):
    payload = valid_payload()
    payload["question_id"] = "not-a-uuid"

    response = api_client.post(
        "/api/v1/learning/attempts",
        json=payload,
    )

    assert response.status_code == 422
    authenticated_client.rpc.assert_not_called()


def test_old_question_fields_are_rejected(
    api_client,
    authenticated_client,
):
    payload = valid_payload()
    payload["concept_id"] = "11111111-1111-4111-8111-111111111111"
    payload["question_text"] = "Client-supplied question"

    response = api_client.post(
        "/api/v1/learning/attempts",
        json=payload,
    )

    assert response.status_code == 422
    authenticated_client.rpc.assert_not_called()


def test_unknown_question_id_is_not_evaluated(
    api_client,
    authenticated_client,
):
    question_query = authenticated_client.question_query
    question_query.execute.return_value = SimpleNamespace(data=[])

    response = api_client.post(
        "/api/v1/learning/attempts",
        json=valid_payload(),
    )

    assert response.status_code == 404
    authenticated_client.evaluator.evaluate.assert_not_called()
    authenticated_client.rpc.assert_not_called()


def test_missing_answer_is_rejected(
    api_client,
    authenticated_client,
):
    payload = valid_payload()
    del payload["student_answer"]

    response = api_client.post(
        "/api/v1/learning/attempts",
        json=payload,
    )

    assert response.status_code == 422
    authenticated_client.rpc.assert_not_called()


def test_missing_reasoning_is_rejected(
    api_client,
    authenticated_client,
):
    payload = valid_payload()
    del payload["reasoning"]

    response = api_client.post(
        "/api/v1/learning/attempts",
        json=payload,
    )

    assert response.status_code == 422
    authenticated_client.rpc.assert_not_called()

def test_next_question_requires_authentication(api_client, mock_supabase):
    assert mock_supabase is not None
    response = api_client.get("/api/v1/learning/next-question")

    assert response.status_code == 401


def test_authenticated_student_receives_adaptive_question(
    api_client,
    authenticated_client,
):
    question_query = MagicMock()
    mastery_query = MagicMock()
    attempt_query = MagicMock()
    prerequisite_query = MagicMock()

    authenticated_client.table.side_effect = [
        question_query,
        mastery_query,
        attempt_query,
        prerequisite_query,
    ]

    for query in (
        question_query,
        mastery_query,
        attempt_query,
        prerequisite_query,
    ):
        query.select.return_value = query
        query.eq.return_value = query

    question_query.execute.return_value = SimpleNamespace(
        data=[
            {
                "id": "22222222-2222-4222-8222-222222222222",
                "concept_id": "11111111-1111-4111-8111-111111111111",
                "question_text": "What is reflection of light?",
                "difficulty": 1,
            }
        ]
    )
    mastery_query.execute.return_value = SimpleNamespace(data=[])
    attempt_query.execute.return_value = SimpleNamespace(data=[])
    prerequisite_query.execute.return_value = SimpleNamespace(data=[])

    response = api_client.get("/api/v1/learning/next-question")

    assert response.status_code == 200
    assert response.json() == {
        "question_id": "22222222-2222-4222-8222-222222222222",
        "concept_id": "11111111-1111-4111-8111-111111111111",
        "question_text": "What is reflection of light?",
        "difficulty": 1,
    }


def test_next_question_does_not_expose_answer_key(
    api_client,
    authenticated_client,
):
    question_query = MagicMock()
    mastery_query = MagicMock()
    attempt_query = MagicMock()
    prerequisite_query = MagicMock()

    authenticated_client.table.side_effect = [
        question_query,
        mastery_query,
        attempt_query,
        prerequisite_query,
    ]

    for query in (
        question_query,
        mastery_query,
        attempt_query,
        prerequisite_query,
    ):
        query.select.return_value = query
        query.eq.return_value = query

    question_query.execute.return_value = SimpleNamespace(
        data=[
            {
                "id": "22222222-2222-4222-8222-222222222222",
                "concept_id": "11111111-1111-4111-8111-111111111111",
                "question_text": "What is reflection of light?",
                "difficulty": 1,
            }
        ]
    )
    mastery_query.execute.return_value = SimpleNamespace(data=[])
    attempt_query.execute.return_value = SimpleNamespace(data=[])
    prerequisite_query.execute.return_value = SimpleNamespace(data=[])

    response = api_client.get("/api/v1/learning/next-question")

    assert response.status_code == 200
    body = response.json()

    assert "expected_answer" not in body
    assert "acceptable_answers" not in body
    assert "grading_rubric" not in body
    assert "misconception_targets" not in body


def test_next_question_returns_404_when_no_questions_exist(
    api_client,
    authenticated_client,
):
    question_query = MagicMock()
    mastery_query = MagicMock()
    attempt_query = MagicMock()
    prerequisite_query = MagicMock()

    authenticated_client.table.side_effect = [
        question_query,
        mastery_query,
        attempt_query,
        prerequisite_query,
    ]

    for query in (
        question_query,
        mastery_query,
        attempt_query,
        prerequisite_query,
    ):
        query.select.return_value = query
        query.eq.return_value = query

    question_query.execute.return_value = SimpleNamespace(data=[])
    mastery_query.execute.return_value = SimpleNamespace(data=[])
    attempt_query.execute.return_value = SimpleNamespace(data=[])
    prerequisite_query.execute.return_value = SimpleNamespace(data=[])

    response = api_client.get("/api/v1/learning/next-question")

    assert response.status_code == 404
    assert response.json()["detail"] == "No active questions are available."


def test_next_question_returns_503_when_database_fails(
    api_client,
    authenticated_client,
):
    authenticated_client.table.side_effect = RuntimeError(
        "Database connection failed"
    )

    response = api_client.get("/api/v1/learning/next-question")

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "Adaptive question data is unavailable."
    )
