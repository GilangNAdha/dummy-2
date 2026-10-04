# perhitungan ringkasan dashboard dan laporan
#
# Seluruh penjumlahan dikerjakan di sini, bukan di frontend. Angka yang
# dikirim ke klien selalu berasal dari data mentah pada tabel, sehingga tidak
# ada kolom turunan yang bisa basi karena dihitung di dua tempat.
from datetime import date, timedelta

from app.core.errors import AppError
from app.core.supabase_client import rest_select

KOLOM_TRANSAKSI = "id,type,amount,txn_date,category_id,member_id,account_id,merchant,notes"


def awal_dan_akhir_bulan(bulan: str) -> tuple[str, str]:
    """Ubah 2026-09 menjadi 2026-09-01 dan 2026-09-30."""
    try:
        tahun, angka_bulan = (int(bagian) for bagian in str(bulan).split("-"))
        awal = date(tahun, angka_bulan, 1)
    except (AttributeError, TypeError, ValueError):
        raise AppError(400, "VALIDATION_ERROR", "Format bulan harus YYYY-MM, misalnya 2026-09.")
    akhir = date(tahun + 1, 1, 1) - timedelta(days=1) if angka_bulan == 12 else date(tahun, angka_bulan + 1, 1) - timedelta(days=1)
    return awal.isoformat(), akhir.isoformat()


def periksa_tanggal(nilai: str, nama: str) -> str:
    """Pastikan tanggal berformat YYYY-MM-DD."""
    try:
        return date.fromisoformat(str(nilai)).isoformat()
    except (TypeError, ValueError):
        raise AppError(400, "VALIDATION_ERROR", f"Tanggal {nama} harus berformat YYYY-MM-DD.")


async def transaksi_rentang(token: str, household_id: str, dari: str, sampai: str) -> list[dict]:
    """Transaksi mentah pada satu rentang tanggal, baris terhapus lunak tidak ikut."""
    return await rest_select(
        "transactions",
        {
            "select": KOLOM_TRANSAKSI,
            "household_id": f"eq.{household_id}",
            "deleted_at": "is.null",
            "txn_date": [f"gte.{dari}", f"lte.{sampai}"],
            "order": "txn_date.asc",
        },
        token,
    )


async def peran_pengguna(token: str, household_id: str, user_id: str | None) -> str | None:
    """Peran pengguna pada satu rumah tangga, atau None bila bukan anggota."""
    baris = await rest_select(
        "household_members",
        {
            "household_id": f"eq.{household_id}",
            "user_id": f"eq.{user_id or ''}",
            "select": "role,display_name",
            "limit": 1,
        },
        token,
    )
    return baris[0]["role"] if baris else None


def _total(baris: list[dict], tipe: str) -> int:
    return sum(int(b.get("amount") or 0) for b in baris if b.get("type") == tipe)


async def ringkasan(token: str, household_id: str, bulan: str) -> dict:
    """Ringkasan bulan berjalan, yaitu pemasukan, pengeluaran, pemakaian anggaran, dan tabungan."""
    dari, sampai = awal_dan_akhir_bulan(bulan)
    baris = await transaksi_rentang(token, household_id, dari, sampai)

    pemasukan = _total(baris, "income")
    pengeluaran = _total(baris, "expense")

    anggaran = await rest_select(
        "budgets",
        {"household_id": f"eq.{household_id}", "period_month": f"eq.{dari}", "select": "category_id,limit_amount"},
        token,
    )
    batas = sum(int(a.get("limit_amount") or 0) for a in anggaran)
    kategori_beranggaran = {a.get("category_id") for a in anggaran}
    terpakai = sum(
        int(b.get("amount") or 0)
        for b in baris
        if b.get("type") == "expense" and b.get("category_id") in kategori_beranggaran
    )

    tujuan = await rest_select("goals", {"household_id": f"eq.{household_id}", "select": "id"}, token)
    terkumpul = 0
    if tujuan:
        daftar_id = ",".join(t["id"] for t in tujuan)
        setoran = await rest_select(
            "goal_contributions", {"goal_id": f"in.({daftar_id})", "select": "amount"}, token
        )
        terkumpul = sum(int(s.get("amount") or 0) for s in setoran)

    return {
        "bulan": bulan,
        "pemasukan": pemasukan,
        "pengeluaran": pengeluaran,
        "selisih": pemasukan - pengeluaran,
        "batas_anggaran": batas,
        "anggaran_terpakai": terpakai,
        "anggaran_tersisa": batas - terpakai,
        "tabungan_terkumpul": terkumpul,
    }


async def arus_kas(token: str, household_id: str, dari: str, sampai: str) -> list[dict]:
    """Arus kas per bulan pada satu rentang tanggal."""
    baris = await transaksi_rentang(token, household_id, dari, sampai)
    per_bulan: dict[str, dict] = {}
    for b in baris:
        kunci = str(b.get("txn_date") or "")[:7]
        sel = per_bulan.setdefault(kunci, {"bulan": kunci, "pemasukan": 0, "pengeluaran": 0})
        if b.get("type") == "income":
            sel["pemasukan"] += int(b.get("amount") or 0)
        elif b.get("type") == "expense":
            sel["pengeluaran"] += int(b.get("amount") or 0)
    hasil = []
    for kunci in sorted(per_bulan):
        sel = per_bulan[kunci]
        sel["selisih"] = sel["pemasukan"] - sel["pengeluaran"]
        hasil.append(sel)
    return hasil


async def rekap_kategori(token: str, household_id: str, dari: str, sampai: str) -> list[dict]:
    """Rekap pengeluaran per kategori, dari yang terbesar."""
    baris = await transaksi_rentang(token, household_id, dari, sampai)
    kategori = await rest_select("categories", {"household_id": f"eq.{household_id}", "select": "id,name"}, token)
    nama = {k["id"]: k["name"] for k in kategori}

    total: dict[str, int] = {}
    for b in baris:
        if b.get("type") != "expense":
            continue
        kunci = b.get("category_id") or ""
        total[kunci] = total.get(kunci, 0) + int(b.get("amount") or 0)

    hasil = [
        {"category_id": kunci or None, "nama": nama.get(kunci, "Tanpa kategori"), "total": nilai}
        for kunci, nilai in total.items()
    ]
    hasil.sort(key=lambda x: x["total"], reverse=True)
    return hasil


async def rekap_anggota(token: str, household_id: str, dari: str, sampai: str) -> list[dict]:
    """Rekap pengeluaran per anggota, dari yang terbesar."""
    baris = await transaksi_rentang(token, household_id, dari, sampai)
    anggota = await rest_select(
        "household_members", {"household_id": f"eq.{household_id}", "select": "id,display_name"}, token
    )
    nama = {a["id"]: a["display_name"] for a in anggota}

    total: dict[str, int] = {}
    for b in baris:
        if b.get("type") != "expense":
            continue
        kunci = b.get("member_id") or ""
        total[kunci] = total.get(kunci, 0) + int(b.get("amount") or 0)

    hasil = [
        {"member_id": kunci or None, "nama": nama.get(kunci, "Tanpa anggota"), "total": nilai}
        for kunci, nilai in total.items()
    ]
    hasil.sort(key=lambda x: x["total"], reverse=True)
    return hasil


def _aman(nilai) -> str:
    """Bungkus nilai CSV yang memuat koma, tanda kutip, atau baris baru."""
    teks = "" if nilai is None else str(nilai)
    if any(x in teks for x in (",", '"', "\n")):
        return '"' + teks.replace('"', '""') + '"'
    return teks


async def berkas_csv(token: str, household_id: str, dari: str, sampai: str) -> str:
    """Berkas CSV transaksi, dibuat backend, siap diunduh pengguna."""
    baris = await transaksi_rentang(token, household_id, dari, sampai)
    kategori = await rest_select("categories", {"household_id": f"eq.{household_id}", "select": "id,name"}, token)
    anggota = await rest_select(
        "household_members", {"household_id": f"eq.{household_id}", "select": "id,display_name"}, token
    )
    nama_kategori = {k["id"]: k["name"] for k in kategori}
    nama_anggota = {a["id"]: a["display_name"] for a in anggota}

    tajuk = "tanggal,jenis,kategori,anggota,merchant,catatan,nominal"
    isi = [tajuk]
    for b in baris:
        isi.append(
            ",".join(
                [
                    _aman(b.get("txn_date")),
                    _aman(b.get("type")),
                    _aman(nama_kategori.get(b.get("category_id"), "")),
                    _aman(nama_anggota.get(b.get("member_id"), "")),
                    _aman(b.get("merchant")),
                    _aman(b.get("notes")),
                    _aman(b.get("amount")),
                ]
            )
        )
    return "\n".join(isi) + "\n"
