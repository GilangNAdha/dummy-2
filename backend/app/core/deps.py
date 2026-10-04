# dependensi autentikasi
from typing import Any

import jwt
from fastapi import Header
from jwt import PyJWKClient

from app.core.config import get_settings
from app.core.errors import unauthenticated

_pemegang_kunci: PyJWKClient | None = None


def _buka_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    if settings.supabase_jwt_secret:
        return jwt.decode(token, settings.supabase_jwt_secret, algorithms=["HS256"], audience="authenticated")
    if not settings.supabase_jwks_url:
        raise unauthenticated()
    global _pemegang_kunci
    if _pemegang_kunci is None:
        _pemegang_kunci = PyJWKClient(settings.supabase_jwks_url)
    kunci = _pemegang_kunci.get_signing_key_from_jwt(token).key
    return jwt.decode(token, kunci, algorithms=["ES256", "RS256"], audience="authenticated")


def _ambil_token(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise unauthenticated()
    return authorization.split(" ", 1)[1].strip()


async def get_access_token(authorization: str | None = Header(default=None)) -> str:
    """Token asli dipakai untuk memanggil PostgREST agar kebijakan RLS berlaku."""
    return _ambil_token(authorization)


async def get_current_user(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    token = _ambil_token(authorization)
    try:
        return _buka_token(token)
    except Exception:
        raise unauthenticated()
