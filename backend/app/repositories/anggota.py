# baca peran pengguna di household_members (tabel milik Nizar, hanya dibaca)
# Penulis: Gilang Nur Adha
from app.core.supabase_client import rest_select


async def peran(token: str, household_id: str, user_id: str | None) -> str | None:
    baris = await rest_select(
        "household_members",
        {"household_id": f"eq.{household_id}", "user_id": f"eq.{user_id or ''}", "select": "role", "limit": 1},
        token,
    )
    return baris[0]["role"] if baris else None
