from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
        "application": "LearnLoop AI",
        "version": "0.1.0",
    }
