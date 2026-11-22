from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest  # pyright: ignore[reportMissingImports]
from fastapi import HTTPException  # pyright: ignore[reportMissingImports]
from fastapi.security import HTTPAuthorizationCredentials  # pyright: ignore[reportMissingImports]

from app.api.dependencies import get_current_user  # pyright: ignore[reportAttributeAccessIssue]


def test_valid_bearer_token_returns_authenticated_user():
    client = MagicMock()
    expected_user = SimpleNamespace(id="authenticated-student-123")
    client.auth.get_user.return_value = SimpleNamespace(user=expected_user)

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="valid-access-token",
    )

    user = get_current_user(credentials, client)

    assert user.id == "authenticated-student-123"
    client.auth.get_user.assert_called_once_with("valid-access-token")


def test_missing_credentials_are_rejected():
    client = MagicMock()

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(None, client)

    assert exc_info.value.status_code == 401
    client.auth.get_user.assert_not_called()


def test_invalid_token_is_rejected():
    client = MagicMock()
    client.auth.get_user.side_effect = Exception("Invalid JWT")

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="invalid-access-token",
    )

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(credentials, client)

    assert exc_info.value.status_code == 401


def test_empty_authenticated_user_is_rejected():
    client = MagicMock()
    client.auth.get_user.return_value = SimpleNamespace(user=None)

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="valid-access-token",
    )

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(credentials, client)

    assert exc_info.value.status_code == 401
