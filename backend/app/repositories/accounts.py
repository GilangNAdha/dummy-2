# query CRUD dan agregasi saldo dompet
# Penulis: Gilang Nur Adha
from app.core.errors import AppError
from app.core.supabase_client import rest_delete, rest_hitung, rest_insert, rest_patch, rest_select
from app.repositories._bersama import tabel_belum_ada

TABEL = "accounts"
KOLOM = "id,household_id,name,type,provider,opening_balance,is_active,created_at,updated_at"


async def daftar(token: str, saring: dict, order: str, limit: int, offset: int) -> tuple[list, int]:
    baris = await rest_select(TABEL, {**saring, "select": KOLOM, "order": order, "limit": limit, "offset": offset}, token)
    total = await rest_hitung(TABEL, saring, token)
    return baris, total


async def ambil(token: str, account_id: str) -> dict | None:
    baris = await rest_select(TABEL, {"id": f"eq.{account_id}", "select": KOLOM, "limit": 1}, token)
    return baris[0] if baris else None


async def nama_dipakai(token: str, household_id: str, name: str, kecuali: str | None = None) -> bool:
    params = {"household_id": f"eq.{household_id}", "name": f"eq.{name}", "select": "id", "limit": 1}
    if kecuali:
        params["id"] = f"neq.{kecuali}"
    return bool(await rest_select(TABEL, params, token))


async def tambah(token: str, data: dict) -> dict:
    baris = await rest_insert(TABEL, data, token)
    return baris[0] if baris else data


async def ubah(token: str, account_id: str, perubahan: dict) -> dict | None:
    baris = await rest_patch(TABEL, {"id": f"eq.{account_id}"}, perubahan, token)
    return baris[0] if baris else None


async def hapus(token: str, account_id: str) -> None:
    await rest_delete(TABEL, {"id": f"eq.{account_id}"}, token)


async def transaksi_dompet(token: str, household_id: str, account_ids: list[str]) -> list[dict]:
    """Satu query untuk semua dompet: transaksi aktif yang menyentuh dompet sebagai asal atau tujuan."""
    if not account_ids:
        return []
    ids = ",".join(account_ids)
    params = {
        "household_id": f"eq.{household_id}",
        "deleted_at": "is.null",
        "or": f"(account_id.in.({ids}),to_account_id.in.({ids}))",
        "select": "account_id,to_account_id,type,amount",
    }
    try:
        return await rest_select("transactions", params, token)
    except AppError as galat:
        if tabel_belum_ada(galat):
            return []
        raise


async def jumlah_rujukan(token: str, account_id: str) -> int:
    """Berapa baris transactions dan goal_contributions yang masih merujuk dompet."""
    total = 0
    for tabel, saring in (
        ("transactions", {"or": f"(account_id.eq.{account_id},to_account_id.eq.{account_id})"}),
        ("goal_contributions", {"account_id": f"eq.{account_id}"}),
    ):
        try:
            total += await rest_hitung(tabel, saring, token)
        except AppError as galat:
            if not tabel_belum_ada(galat):
                raise
    return total
