from unittest.mock import patch

import pytest  # pyright: ignore[reportMissingImports]

from app.core.config import Settings
from app.services.supabase import create_supabase_client  # pyright: ignore[reportMissingImports]


def test_supabase_client_requires_credentials():
    settings = Settings(_env_file=None)

    with pytest.raises(
        RuntimeError,
        match="SUPABASE_URL and SUPABASE_SECRET_KEY",
    ):
        create_supabase_client(settings)


def test_supabase_client_uses_server_credentials():
    settings = Settings(
        _env_file=None,
        supabase_url="https://example.supabase.co",
        supabase_secret_key="test-secret-key",
    )

    expected_client = object()

    with patch(
        "app.services.supabase.create_client",
        return_value=expected_client,
    ) as mock_create_client:
        client = create_supabase_client(settings)

    assert client is expected_client
    mock_create_client.assert_called_once_with(
        "https://example.supabase.co",
        "test-secret-key",
    )
