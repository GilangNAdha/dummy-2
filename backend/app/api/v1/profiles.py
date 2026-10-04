# endpoint profil pengguna
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.core.deps import get_access_token, get_current_user
from app.core.errors import AppError, not_found
from app.core.supabase_client import rest_patch, rest_select

router = APIRouter(prefix="/profiles", tags=["profil"])

KOLOM = "id,email,full_name,avatar_emoji,created_at"


class ProfilUbah(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    avatar_emoji: str | None = Field(default=None, max_length=8)


@router.get("/me")
async def profil_saya(user: dict = Depends(get_current_user), token: str = Depends(get_access_token)) -> dict:
    """Profil milik pemilik token."""
    baris = await rest_select("profiles", {"id": f"eq.{user.get('sub')}", "select": KOLOM, "limit": 1}, token)
    if not baris:
        raise not_found("Profil tidak ditemukan.")
    return {"data": baris[0]}


@router.patch("/me")
async def ubah_profil(
    payload: ProfilUbah,
    user: dict = Depends(get_current_user),
    token: str = Depends(get_access_token),
) -> dict:
    """Ubah nama lengkap atau ikon avatar sendiri."""
    perubahan = payload.model_dump(exclude_none=True)
    if not perubahan:
        raise AppError(400, "VALIDATION_ERROR", "Tidak ada kolom yang diubah.")

    baris = await rest_patch("profiles", {"id": f"eq.{user.get('sub')}"}, perubahan, token)
    if not baris:
        raise not_found("Profil tidak ditemukan.")
    return {"data": baris[0]}
