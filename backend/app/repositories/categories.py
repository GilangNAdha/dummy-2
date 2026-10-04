# query CRUD kategori
# Penulis: Gilang Nur Adha
from app.core.errors import AppError
from app.core.supabase_client import rest_delete, rest_hitung, rest_insert, rest_patch, rest_select
from app.repositories._bersama import tabel_belum_ada

TABEL = "categories"
KOLOM = "id,household_id,name,kind,icon,color,is_system,is_archived,created_at,updated_at"


def saring_terlihat(household_id: str) -> dict:
    """Kategori sistem (household_id NULL) ditambah kategori milik rumah tangga."""
    return {"or": f"(household_id.is.null,household_id.eq.{household_id})"}


async def daftar(token: str, saring: dict, order: str, limit: int, offset: int) -> tuple[list, int]:
    baris = await rest_select(TABEL, {**saring, "select": KOLOM, "order": order, "limit": limit, "offset": offset}, token)
    total = await rest_hitung(TABEL, saring, token)
    return baris, total


async def ambil(token: str, category_id: str) -> dict | None:
    baris = await rest_select(TABEL, {"id": f"eq.{category_id}", "select": KOLOM, "limit": 1}, token)
    return baris[0] if baris else None


async def cari_nama(token: str, household_id: str, name: str, kecuali: str | None = None) -> list[dict]:
    """Kategori bernama sama, baik milik rumah tangga maupun kategori sistem."""
    params = {**saring_terlihat(household_id), "name": f"eq.{name}", "select": "id,kind,is_system"}
    if kecuali:
        params["id"] = f"neq.{kecuali}"
    return await rest_select(TABEL, params, token)


async def tambah(token: str, data: dict) -> dict:
    baris = await rest_insert(TABEL, data, token)
    return baris[0] if baris else data


async def ubah(token: str, category_id: str, perubahan: dict) -> dict | None:
    baris = await rest_patch(TABEL, {"id": f"eq.{category_id}"}, perubahan, token)
    return baris[0] if baris else None


async def hapus(token: str, category_id: str) -> None:
    await rest_delete(TABEL, {"id": f"eq.{category_id}"}, token)


async def jumlah_transaksi(token: str, category_id: str) -> int:
    try:
        return await rest_hitung("transactions", {"category_id": f"eq.{category_id}"}, token)
    except AppError as galat:
        if tabel_belum_ada(galat):
            return 0
        raise
