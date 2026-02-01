from fastapi import Request, HTTPException
from aiohttp import ClientSession, ClientTimeout
from jose import jwt, JWTError

from app.settings import settings


class AuthClient:
    def __init__(self, auth_path: str):
        self.auth_path = auth_path

    async def authenticate(self, request: Request) -> dict:
        if not request.cookies:
            raise HTTPException(status_code=401, detail="Not authenticated")

        async with ClientSession() as session:
            try:
                response = await session.post(
                    self.auth_path,
                    cookies=request.cookies,
                    timeout=ClientTimeout(total=3),
                )
            except Exception:
                raise HTTPException(status_code=503, detail="Auth service unavailable")

        if not response.ok:
            raise HTTPException(status_code=401, detail="Invalid session")

        try:
            return jwt.get_unverified_claims(
                request.cookies["access-token"]
            )
        except (JWTError, KeyError, ValueError):
            raise HTTPException(status_code=401, detail="Invalid token")


auth_client = AuthClient(settings.auth_api_access_token_check_url)


async def get_current_user_id(
    request: Request,
) -> str:
    payload = await auth_client.authenticate(request)
    return payload["sub"]


async def require_admin(
    request: Request,
) -> str:
    payload = await auth_client.authenticate(request)

    if payload.get("role") != "superuser":
        raise HTTPException(status_code=403, detail="Admin only")

    return payload["sub"]
