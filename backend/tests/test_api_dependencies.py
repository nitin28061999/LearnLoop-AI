
from unittest.mock import patch

import pytest  # pyright: ignore[reportMissingImports]
from fastapi import HTTPException  # pyright: ignore[reportMissingImports]
from pydantic import SecretStr

from app.api.dependencies import get_supabase
from app.core.config import Settings


def test_get_supabase_uses_application_settings():
    settings = Settings(
        _env_file=None,
        supabase_url="https://example.supabase.co",
        supabase_secret_key="test-secret-key",
    )
    expected_client = object()

    with (
        patch("app.api.dependencies.get_settings", return_value=settings),
        patch(
            "app.api.dependencies.create_supabase_client",
            return_value=expected_client,
        ) as mock_create_client,
    ):
        client = get_supabase()

    assert client is expected_client
    mock_create_client.assert_called_once_with(settings)


def test_get_answer_evaluator_creates_gemini_evaluator():
    settings = Settings(
        _env_file=None,
        gemini_api_key=SecretStr("test-gemini-key"),
    )
    expected_evaluator = object()

    with (
        patch("app.api.dependencies.get_settings", return_value=settings),
        patch("app.api.dependencies.genai.Client") as mock_client,
        patch(
            "app.api.dependencies.GeminiAnswerEvaluator",
            return_value=expected_evaluator,
        ) as mock_evaluator,
    ):
        from app.api.dependencies import get_answer_evaluator

        evaluator = get_answer_evaluator()

    assert evaluator is expected_evaluator
    mock_client.assert_called_once_with(api_key="test-gemini-key")
    mock_evaluator.assert_called_once_with(
        client=mock_client.return_value,
        model="gemini-2.5-flash",
    )


def test_get_answer_evaluator_requires_api_key():
    settings = Settings(_env_file=None, gemini_api_key=None)

    with patch("app.api.dependencies.get_settings", return_value=settings):
        from app.api.dependencies import get_answer_evaluator

        with pytest.raises(HTTPException) as exc_info:
            get_answer_evaluator()

    assert exc_info.value.status_code == 503
