# endpoint ringkasan dashboard dan laporan
from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

from app.core.deps import get_access_token, get_current_user
from app.core.errors import forbidden
from app.services import report_service as layanan

router = APIRouter(tags=["ringkasan dan laporan"])

PERAN_BOLEH_LAPORAN = ("ayah", "ibu")


async def _wajib_peran_laporan(household_id: str, user: dict, token: str) -> None:
    """Laporan hanya untuk Ayah dan Ibu, sama seperti aturan pada dokumen kontrak."""
    peran = await layanan.peran_pengguna(token, household_id, user.get("sub"))
    if peran is None:
        raise forbidden("Kamu bukan anggota rumah tangga itu.")
    if peran not in PERAN_BOLEH_LAPORAN:
        raise forbidden("Laporan hanya untuk Ayah dan Ibu.")


def _rentang_default(dari: str | None, sampai: str | None) -> tuple[str, str]:
    awal = date.today().replace(day=1).isoformat()
    akhir = date.today().isoformat()
    return (
        layanan.periksa_tanggal(dari or awal, "dari"),
        layanan.periksa_tanggal(sampai or akhir, "sampai"),
    )


@router.get("/dashboard/summary")
async def ringkasan_dashboard(
    household_id: str,
    bulan: str | None = Query(default=None, description="Format YYYY-MM, kosong berarti bulan berjalan."),
    user: dict = Depends(get_current_user),
    token: str = Depends(get_access_token),
) -> dict:
    """Ringkasan bulan berjalan, boleh dibaca semua anggota rumah tangga."""
    bulan_dipakai = bulan or date.today().strftime("%Y-%m")
    return {"data": await layanan.ringkasan(token, household_id, bulan_dipakai)}


@router.get("/reports/cashflow")
async def laporan_arus_kas(
    household_id: str,
    dari: str | None = Query(default=None, alias="from"),
    sampai: str | None = Query(default=None, alias="to"),
    user: dict = Depends(get_current_user),
    token: str = Depends(get_access_token),
) -> dict:
    """Arus kas per bulan pada satu rentang tanggal."""
    await _wajib_peran_laporan(household_id, user, token)
    awal, akhir = _rentang_default(dari, sampai)
    return {"data": await layanan.arus_kas(token, household_id, awal, akhir), "meta": {"dari": awal, "sampai": akhir}}


@router.get("/reports/categories")
async def laporan_kategori(
    household_id: str,
    dari: str | None = Query(default=None, alias="from"),
    sampai: str | None = Query(default=None, alias="to"),
    user: dict = Depends(get_current_user),
    token: str = Depends(get_access_token),
) -> dict:
    """Rekap pengeluaran per kategori pada satu rentang tanggal."""
    await _wajib_peran_laporan(household_id, user, token)
    awal, akhir = _rentang_default(dari, sampai)
    return {"data": await layanan.rekap_kategori(token, household_id, awal, akhir), "meta": {"dari": awal, "sampai": akhir}}


@router.get("/reports/members")
async def laporan_anggota(
    household_id: str,
    dari: str | None = Query(default=None, alias="from"),
    sampai: str | None = Query(default=None, alias="to"),
    user: dict = Depends(get_current_user),
    token: str = Depends(get_access_token),
) -> dict:
    """Rekap pengeluaran per anggota pada satu rentang tanggal."""
    await _wajib_peran_laporan(household_id, user, token)
    awal, akhir = _rentang_default(dari, sampai)
    return {"data": await layanan.rekap_anggota(token, household_id, awal, akhir), "meta": {"dari": awal, "sampai": akhir}}


@router.get("/reports/export.csv")
async def ekspor_transaksi(
    household_id: str,
    dari: str | None = Query(default=None, alias="from"),
    sampai: str | None = Query(default=None, alias="to"),
    user: dict = Depends(get_current_user),
    token: str = Depends(get_access_token),
) -> Response:
    """Unduh transaksi sebagai berkas CSV yang dibuat backend."""
    await _wajib_peran_laporan(household_id, user, token)
    awal, akhir = _rentang_default(dari, sampai)
    teks = await layanan.berkas_csv(token, household_id, awal, akhir)
    return Response(
        content=teks,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="transaksi_{awal}_{akhir}.csv"'},
    )
