import httpx
from fastapi import HTTPException, status
from app.config import settings

TURNSTILE_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


async def verify_turnstile(token: str) -> None:
    if not token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Turnstile token is required")

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                TURNSTILE_VERIFY_URL,
                data={"secret": settings.turnstile_secret_key, "response": token},
                timeout=10.0,
            )
            result = resp.json()
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Failed to contact Turnstile verification service",
            ) from exc

    if not result.get("success"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Turnstile verification failed")
