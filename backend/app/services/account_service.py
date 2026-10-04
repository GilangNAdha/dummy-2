# aturan bisnis dompet dan perhitungan saldo berjalan (current_balance)
# Penulis: Gilang Nur Adha
from app.core.errors import AppError, conflict, forbidden, not_found
from app.repositories import accounts as repo
from app.services import akses
from app.services.urutan import ke_order

KOLOM_SORT = {"name", "type", "created_at", "opening_balance"}


# ---------- perhitungan murni (dapat diuji tanpa HTTP) ----------
def hitung_saldo(dompet: list[dict], transaksi: list[dict]) -> dict[str, int]:
    """
    current_balance = opening_balance
        + income ke dompet - expense dari dompet
        - transfer keluar (account_id) + transfer masuk (to_account_id)
    Transfer satu baris, bukan pengeluaran. Transaksi terhapus (deleted_at) sudah disaring repository,
    tetapi tetap diabaikan di sini bila ikut terbawa.
    """
    saldo = {d["id"]: int(d.get("opening_balance") or 0) for d in dompet}
    for t in transaksi:
        if t.get("deleted_at"):
            continue
        jumlah = int(t["amount"])
        asal, tujuan, jenis = t.get("account_id"), t.get("to_account_id"), t.get("type")
        if jenis == "income" and asal in saldo:
            saldo[asal] += jumlah
        elif jenis == "expense" and asal in saldo:
            saldo[asal] -= jumlah
        elif jenis == "transfer":
            if asal in saldo:
                saldo[asal] -= jumlah
            if tujuan in saldo:
                saldo[tujuan] += jumlah
    return saldo


async def _dengan_saldo(token: str, household_id: str, dompet: list[dict]) -> list[dict]:
    transaksi = await repo.transaksi_dompet(token, household_id, [d["id"] for d in dompet])
    saldo = hitung_saldo(dompet, transaksi)
    return [{**d, "current_balance": saldo[d["id"]]} for d in dompet]


async def _ambil_milik(token: str, account_id: str, user: dict) -> tuple[dict, str]:
    """Dompet milik rumah tangga lain dijawab 404 agar keberadaannya tidak bocor."""
    dompet = await repo.ambil(token, account_id)
    if not dompet:
        raise not_found("Dompet tidak ditemukan.")
    peran = await akses.peran(token, dompet["household_id"], user)
    if peran is None:
        raise not_found("Dompet tidak ditemukan.")
    return dompet, peran


async def _cek_nama(token: str, household_id: str, name: str, kecuali: str | None = None) -> None:
    if await repo.nama_dipakai(token, household_id, name, kecuali):
        raise conflict("Nama dompet sudah dipakai.")


# ---------- operasi ----------
async def daftar(token, user, household_id, jenis, is_active, sort, limit, offset) -> tuple[list, int]:
    await akses.wajib_anggota(token, household_id, user)
    saring = {"household_id": f"eq.{household_id}"}
    if jenis:
        saring["type"] = f"eq.{jenis}"
    if is_active is not None:
        saring["is_active"] = f"eq.{str(is_active).lower()}"
    order = ke_order(sort, KOLOM_SORT, "created_at.desc")
    baris, total = await repo.daftar(token, saring, order, limit, offset)
    return await _dengan_saldo(token, household_id, baris), total


async def detail(token, user, account_id) -> dict:
    dompet, _ = await _ambil_milik(token, account_id, user)
    return (await _dengan_saldo(token, dompet["household_id"], [dompet]))[0]


async def tambah(token, user, data: dict) -> dict:
    await akses.wajib_penulis(token, data["household_id"], user)
    data = {**data, "name": data["name"].strip()}
    await _cek_nama(token, data["household_id"], data["name"])
    baru = await repo.tambah(token, data)
    return {**baru, "current_balance": int(baru.get("opening_balance") or 0)}


async def ubah(token, user, account_id, perubahan: dict) -> dict:
    if not perubahan:
        raise AppError(400, "VALIDATION_ERROR", "Tidak ada kolom yang diubah.")
    kosong = [k for k in ("name", "type", "opening_balance", "is_active") if k in perubahan and perubahan[k] is None]
    if kosong:
        raise AppError(400, "VALIDATION_ERROR", "Kolom wajib tidak boleh null.",
                       [{"field": k, "issue": "tidak boleh null"} for k in kosong])
    dompet, peran = await _ambil_milik(token, account_id, user)
    if peran not in akses.PERAN_PENULIS:
        raise forbidden("Hanya Ayah dan Ibu yang boleh mengubah dompet.")
    if "name" in perubahan:
        perubahan = {**perubahan, "name": perubahan["name"].strip()}
        await _cek_nama(token, dompet["household_id"], perubahan["name"], kecuali=account_id)
    hasil = await repo.ubah(token, account_id, perubahan)
    if not hasil:
        raise not_found("Dompet tidak ditemukan.")
    return (await _dengan_saldo(token, dompet["household_id"], [hasil]))[0]


async def hapus(token, user, account_id) -> None:
    """
    Anak: 403. Masih dirujuk transaksi atau setoran tujuan: 409 (arsipkan lewat is_active=false).
    Ibu tidak boleh menghapus dompet yang masih bersaldo: 403.
    """
    dompet, peran = await _ambil_milik(token, account_id, user)
    if peran not in akses.PERAN_PENULIS:
        raise forbidden("Hanya Ayah dan Ibu yang boleh menghapus dompet.")
    if await repo.jumlah_rujukan(token, account_id) > 0:
        raise conflict("Dompet masih dipakai transaksi. Arsipkan dengan is_active=false.")
    if peran == "ibu" and int(dompet.get("opening_balance") or 0) != 0:
        raise forbidden("Ibu tidak dapat menghapus dompet yang masih memiliki saldo.")
    await repo.hapus(token, account_id)
