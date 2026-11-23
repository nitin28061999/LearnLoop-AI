from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest  # pyright: ignore[reportMissingImports]

from app.learning.bkt import update_mastery
from app.learning.service import LearningService  # pyright: ignore[reportMissingImports]


def build_mock_client(mastery_rows=None):
    client = MagicMock()

    query = MagicMock()
    query.execute.return_value = SimpleNamespace(
        data=mastery_rows if mastery_rows is not None else []
    )

    (
        client.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value
    ) = query

    rpc_query = MagicMock()
    rpc_query.execute.return_value = SimpleNamespace(data={"success": True})
    client.rpc.return_value = rpc_query

    return client


def test_new_student_starts_with_initial_bkt_mastery():
    client = build_mock_client()
    service = LearningService(client)

    result = service.record_answer(
        student_id="student-123",
        concept_id="concept-456",
        question_text="What is reflection of light?",
        student_answer="Light bounces back from a surface.",
        reasoning="The ray returns after striking the surface.",
        is_correct=True,
    )

    assert result.mastery_before == pytest.approx(0.2)
    assert result.mastery_after == pytest.approx(update_mastery(0.2, True))


def test_existing_student_mastery_is_used():
    client = build_mock_client(
        mastery_rows=[
            {
                "mastery_probability": 0.65,
                "attempts_count": 4,
                "correct_count": 3,
            }
        ]
    )
    service = LearningService(client)

    result = service.record_answer(
        student_id="student-123",
        concept_id="concept-456",
        question_text="Define focal length.",
        student_answer="Distance between pole and focus.",
        reasoning="I used the definition of focal length.",
        is_correct=True,
    )

    assert result.mastery_before == pytest.approx(0.65)
    assert result.mastery_after == pytest.approx(update_mastery(0.65, True))
    client.rpc.assert_called_once()
    _, parameters = client.rpc.call_args.args
    assert parameters["p_expected_attempts_count"] == 4


def test_incorrect_answer_updates_mastery():
    client = build_mock_client()
    service = LearningService(client)

    result = service.record_answer(
        student_id="student-123",
        concept_id="concept-456",
        question_text="What is refraction?",
        student_answer="Reflection of light.",
        reasoning="I confused reflection with refraction.",
        is_correct=False,
    )

    assert result.mastery_after == pytest.approx(update_mastery(0.2, False))


def test_answer_is_saved_through_atomic_database_rpc():
    client = build_mock_client()
    service = LearningService(client)

    service.record_answer(
        student_id="student-123",
        concept_id="concept-456",
        question_text="What is Ohm's law?",
        student_answer="V = IR",
        reasoning="Voltage equals current multiplied by resistance.",
        is_correct=True,
    )

    client.rpc.assert_called_once()

    function_name, parameters = client.rpc.call_args.args

    assert function_name == "record_learning_attempt"
    assert parameters["p_student_id"] == "student-123"
    assert parameters["p_concept_id"] == "concept-456"
    assert parameters["p_is_correct"] is True
    assert parameters["p_mastery_before"] == pytest.approx(0.2)
    assert parameters["p_mastery_after"] == pytest.approx(update_mastery(0.2, True))
    assert parameters["p_expected_attempts_count"] == 0


def test_invalid_answer_type_is_rejected():
    client = build_mock_client()
    service = LearningService(client)

    with pytest.raises(ValueError):
        service.record_answer(
            student_id="student-123",
            concept_id="concept-456",
            question_text="What is current?",
            student_answer="Flow of charge.",
            reasoning="",
            is_correct=1,  # type: ignore
        )

    client.rpc.assert_not_called()
def test_stale_attempt_count_retries_with_latest_mastery():
    client = build_mock_client()

    read_query = (
        client.table.return_value
        .select.return_value
        .eq.return_value
        .eq.return_value
        .limit.return_value
    )

    # First read is stale; the retry reads the updated mastery.
    read_query.execute.side_effect = [
        SimpleNamespace(
            data=[
                {
                    "mastery_probability": 0.65,
                    "attempts_count": 4,
                }
            ]
        ),
        SimpleNamespace(
            data=[
                {
                    "mastery_probability": 0.70,
                    "attempts_count": 5,
                }
            ]
        ),
    ]

    rpc_query = client.rpc.return_value
    rpc_query.execute.side_effect = [
        SimpleNamespace(
            data={"success": False, "reason": "stale_attempt_count"}
        ),
        SimpleNamespace(data={"success": True}),
    ]

    service = LearningService(client)

    result = service.record_answer(
        student_id="student-123",
        concept_id="concept-456",
        question_text="What is Ohm's law?",
        student_answer="V = IR",
        reasoning="Voltage equals current multiplied by resistance.",
        is_correct=True,
    )

    assert client.rpc.call_count == 2
    assert result.mastery_before == pytest.approx(0.70)
    assert result.mastery_after == pytest.approx(
        update_mastery(0.70, True)
    )

    first_parameters = client.rpc.call_args_list[0].args[1]
    second_parameters = client.rpc.call_args_list[1].args[1]

    assert first_parameters["p_expected_attempts_count"] == 4
    assert second_parameters["p_expected_attempts_count"] == 5


def test_repeated_stale_attempts_eventually_raise_error():
    client = build_mock_client()

    rpc_query = client.rpc.return_value
    rpc_query.execute.return_value = SimpleNamespace(
        data={"success": False, "reason": "stale_attempt_count"}
    )

    service = LearningService(client)

    with pytest.raises(RuntimeError, match="concurrency retries"):
        service.record_answer(
            student_id="student-123",
            concept_id="concept-456",
            question_text="What is resistance?",
            student_answer="Opposition to current flow.",
            reasoning="Resistance opposes electric current.",
            is_correct=True,
        )

    assert client.rpc.call_count == 3


def test_learning_service_calculates_and_persists_review_schedule():
    reviewed_at = datetime(2026, 11, 22, 12, 0, tzinfo=UTC)
    client = build_mock_client()
    service = LearningService(client)

    result = service.record_answer(
        student_id="student-123",
        concept_id="concept-456",
        question_text="What is reflection of light?",
        student_answer="Light bounces back from a surface.",
        reasoning="The ray returns after striking the surface.",
        is_correct=True,
        reviewed_at=reviewed_at,
    )

    _, parameters = client.rpc.call_args.args

    assert parameters["p_repetition_count"] == 1
    assert parameters["p_review_interval_days"] == 1
    assert parameters["p_ease_factor"] == pytest.approx(2.6)
    assert parameters["p_next_review_at"] == (
        reviewed_at + timedelta(days=1)
    ).isoformat()
    assert parameters["p_last_reviewed_at"] == reviewed_at.isoformat()

    assert result.review_state.repetition_count == 1
    assert result.review_state.interval_days == 1
