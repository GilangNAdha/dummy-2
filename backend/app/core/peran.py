# pemeriksaan peran anggota rumah tangga (lapis pertama, lapis kedua adalah RLS)
# Penulis: Gilang Nur Adha
from app.core.errors import forbidden
from app.core.supabase_client import rest_select

PERAN_PENULIS = ("ayah", "ibu")


async def ambil_peran(token: str, household_id: str, user_id: str | None) -> str | None:
    """Peran pengguna pada rumah tangga, None bila bukan anggota."""
    baris = await rest_select(
        "household_members",
        {"household_id": f"eq.{household_id}", "user_id": f"eq.{user_id or ''}", "select": "role", "limit": 1},
        token,
    )
    return baris[0]["role"] if baris else None


async def wajib_anggota(token: str, household_id: str, user: dict) -> str:
    peran = await ambil_peran(token, household_id, user.get("sub"))
    if peran is None:
        raise forbidden("Kamu bukan anggota rumah tangga itu.")
    return peran


async def wajib_penulis(token: str, household_id: str, user: dict) -> str:
    """Hanya Ayah dan Ibu yang boleh menambah, mengubah, atau menghapus."""
    peran = await wajib_anggota(token, household_id, user)
    if peran not in PERAN_PENULIS:
        raise forbidden("Hanya Ayah dan Ibu yang boleh mengubah data ini.")
    return peran
