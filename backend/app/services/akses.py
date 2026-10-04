# pemeriksaan peran pada rumah tangga (lapis FastAPI; lapis kedua adalah RLS)
# Sementara sampai dependensi require_role dari Chandra tersedia.
# Penulis: Gilang Nur Adha
from app.core.errors import forbidden
from app.repositories import anggota

PERAN_PENULIS = ("ayah", "ibu")


async def peran(token: str, household_id: str, user: dict) -> str | None:
    return await anggota.peran(token, household_id, user.get("sub"))


async def wajib_anggota(token: str, household_id: str, user: dict) -> str:
    hasil = await peran(token, household_id, user)
    if hasil is None:
        raise forbidden("Kamu bukan anggota rumah tangga itu.")
    return hasil


async def wajib_penulis(token: str, household_id: str, user: dict) -> str:
    hasil = await wajib_anggota(token, household_id, user)
    if hasil not in PERAN_PENULIS:
        raise forbidden("Hanya Ayah dan Ibu yang boleh mengubah data ini.")
    return hasil
