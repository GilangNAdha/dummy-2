# aturan bisnis kategori: kategori sistem, nama ganda, kategori terpakai
# Penulis: Gilang Nur Adha
from app.core.errors import AppError, conflict, forbidden, not_found
from app.repositories import categories as repo
from app.services import akses
from app.services.urutan import ke_order

KOLOM_SORT = {"name", "kind", "created_at"}


async def _ambil_terlihat(token: str, category_id: str, user: dict) -> tuple[dict, str | None]:
    kategori = await repo.ambil(token, category_id)
    if not kategori:
        raise not_found("Kategori tidak ditemukan.")
    if kategori.get("household_id") is None:
        return kategori, None
    peran = await akses.peran(token, kategori["household_id"], user)
    if peran is None:
        raise not_found("Kategori tidak ditemukan.")
    return kategori, peran


async def _ambil_untuk_tulis(token: str, category_id: str, user: dict) -> dict:
    kategori, peran = await _ambil_terlihat(token, category_id, user)
    if kategori.get("is_system") or kategori.get("household_id") is None:
        raise forbidden("Kategori sistem tidak dapat diubah atau dihapus.")
    if peran not in akses.PERAN_PENULIS:
        raise forbidden("Hanya Ayah dan Ibu yang boleh mengubah kategori.")
    return kategori


async def _cek_nama(token, household_id, name, kind, kecuali=None) -> None:
    """Nama unik per rumah tangga, dan tidak boleh menyamai kategori sistem berjenis sama."""
    for baris in await repo.cari_nama(token, household_id, name, kecuali):
        if not baris.get("is_system") or baris.get("kind") == kind:
            raise conflict("Nama kategori sudah dipakai.")


async def daftar(token, user, household_id, kind, is_archived, sort, limit, offset) -> tuple[list, int]:
    await akses.wajib_anggota(token, household_id, user)
    saring = repo.saring_terlihat(household_id)
    if kind:
        saring["kind"] = f"eq.{kind}"
    if is_archived is not None:
        saring["is_archived"] = f"eq.{str(is_archived).lower()}"
    order = ke_order(sort, KOLOM_SORT, "created_at.desc")
    return await repo.daftar(token, saring, order, limit, offset)


async def detail(token, user, category_id) -> dict:
    kategori, _ = await _ambil_terlihat(token, category_id, user)
    return kategori


async def tambah(token, user, data: dict) -> dict:
    await akses.wajib_penulis(token, data["household_id"], user)
    data = {**data, "name": data["name"].strip(), "is_system": False}
    await _cek_nama(token, data["household_id"], data["name"], data["kind"])
    return await repo.tambah(token, data)


async def ubah(token, user, category_id, perubahan: dict) -> dict:
    if not perubahan:
        raise AppError(400, "VALIDATION_ERROR", "Tidak ada kolom yang diubah.")
    kosong = [k for k in ("name", "kind", "color", "is_archived") if k in perubahan and perubahan[k] is None]
    if kosong:
        raise AppError(400, "VALIDATION_ERROR", "Kolom wajib tidak boleh null.",
                       [{"field": k, "issue": "tidak boleh null"} for k in kosong])
    kategori = await _ambil_untuk_tulis(token, category_id, user)
    if "name" in perubahan:
        perubahan = {**perubahan, "name": perubahan["name"].strip()}
    if "name" in perubahan or "kind" in perubahan:
        await _cek_nama(
            token, kategori["household_id"], perubahan.get("name", kategori["name"]),
            perubahan.get("kind", kategori["kind"]), kecuali=category_id,
        )
    if "kind" in perubahan and perubahan["kind"] != kategori["kind"]:
        if await repo.jumlah_transaksi(token, category_id) > 0:
            raise conflict("Jenis kategori tidak bisa diubah karena sudah dipakai transaksi.")
    hasil = await repo.ubah(token, category_id, perubahan)
    if not hasil:
        raise not_found("Kategori tidak ditemukan.")
    return hasil


async def hapus(token, user, category_id) -> None:
    await _ambil_untuk_tulis(token, category_id, user)
    if await repo.jumlah_transaksi(token, category_id) > 0:
        raise conflict("Kategori masih dipakai transaksi. Arsipkan dengan is_archived=true.")
    await repo.hapus(token, category_id)
