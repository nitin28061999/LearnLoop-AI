
from fastapi import Depends, HTTPException, status  # pyright: ignore[reportMissingImports]
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer  # pyright: ignore[reportMissingImports]
from google import genai  # pyright: ignore[reportAttributeAccessIssue]
from supabase import Client

from app.ai.evaluator import GeminiAnswerEvaluator
from app.core.config import get_settings
from app.services.supabase import create_supabase_client

bearer_scheme = HTTPBearer(auto_error=False)


def get_supabase() -> Client:
    settings = get_settings()
    return create_supabase_client(settings)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    client: Client = Depends(get_supabase),
):
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        response = client.auth.get_user(credentials.credentials)
        user = response.user # pyright: ignore[reportOptionalMemberAccess]
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    if user is None or not getattr(user, "id", None):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def get_answer_evaluator() -> GeminiAnswerEvaluator:
    settings = get_settings()

    if settings.gemini_api_key is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Answer evaluation service is not configured.",
        )

    client = genai.Client(
        api_key=settings.gemini_api_key.get_secret_value()
    )

    return GeminiAnswerEvaluator(
        client=client,
        model="gemini-2.5-flash",
    )
