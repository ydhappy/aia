from fastapi import Header

from app.core.config import settings


class ApiKeyError(Exception):
    pass


async def verify_api_key(x_api_key: str | None = Header(default=None)) -> None:
    if not settings.enable_api_key_auth:
        return
    if not settings.api_key:
        raise ApiKeyError("api_key_not_configured")
    if x_api_key != settings.api_key:
        raise ApiKeyError("invalid_api_key")
