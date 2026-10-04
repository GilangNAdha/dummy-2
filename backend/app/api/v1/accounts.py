# endpoint dompet (accounts)
#
# Pola mengikuti app/api/v1/profiles.py: router tipis, tanpa perhitungan,
# seluruh akses data lewat core/supabase_client.py memakai token asli pengguna
# sehingga kebijakan RLS berlaku sebagai pengguna itu (bukan sebagai admin).
#
# Kontrak umum (Bab 3.1):
#   - nama field sama dengan nama kolom, JSON snake_case
#   - sukses: GET 200, POST 201, PATCH 200, DELETE 200 dengan badan
#     {"data": null, "message": "baris dihapus"}
#   - daftar memakai penolong core/pagination.py: {data, meta, links}
#   - setiap query menyaring household_id
#   - galat dilempar lewat core/errors.py, bukan HTTPException mentah
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from pydantic import BaseModel, ConfigDict, Field, StrictInt

from app.core.deps import get_access_token, get_current_user
from app.core.errors import AppError, conflict, not_found
from app.core.pagination import PageParams, list_response, page_params
from app.core.peran import wajib_penulis
from app.core.supabase_client import (
    KODE_KUNCI_ASING,
    KonflikData,
    rest_delete,
    rest_hitung,
    rest_insert,
    rest_patch,
    rest_select,
)

router = APIRouter(prefix="/accounts", tags=["dompet"])

AccountType = Literal["bank", "cash", "ewallet"]

KOLOM = "id,household_id,name,type,provider,opening_balance,is_active,created_at,updated_at"
SORT_BOLEH = ("created_at", "name", "opening_balance")
SORT_BAWAAN = "created_at:desc"


# ----------------------------------------------------------------- skema Pydantic
# Diletakkan di berkas router, mengikuti pola ProfilUbah pada profiles.py
# (panduan kerja D5: jangan membuat folder app/schemas sebelum disepakati tim).
class _Dasar(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")


class AccountCreate(_Dasar):
    household_id: UUID
    name: str = Field(min_length=1, max_length=80)
    type: AccountType
    provider: str | None = Field(default=None, max_length=60)
    # StrictInt: rupiah penuh, nilai desimal seperti 1000.5 ditolak 400
    opening_balance: StrictInt = Field(default=0, ge=0)
    is_active: bool = True


class AccountUpdate(_Dasar):
    # semua kolom opsional karena PATCH mengubah sebagian
    # (household_id tidak ada di sini, jadi upaya memindahkan dompet ditolak 400)
    name: str | None = Field(default=None, min_length=1, max_length=80)
    type: AccountType | None = None
    provider: str | None = Field(default=None, max_length=60)
    opening_balance: StrictInt | None = Field(default=None, ge=0)
    is_active: bool | None = None


# ------------------------------------------------------------------- penolong
def _urutan(sort: str) -> str:
    """Ubah sort=kolom:asc menjadi bentuk order PostgREST, dibatasi daftar putih."""
    kolom, _, arah = sort.partition(":")
    if kolom not in SORT_BOLEH or arah not in ("asc", "desc", ""):
        raise AppError(
            400,
            "VALIDATION_ERROR",
            "Nilai sort tidak dikenal.",
            [{"field": "sort", "issue": f"pakai salah satu dari {', '.join(SORT_BOLEH)} diikuti :asc atau :desc"}],
        )
    return f"{kolom}.{arah or 'asc'}"


def _penyaring(household_id: UUID, type: str | None, is_active: bool | None) -> dict:
    """Penyaring PostgREST. household_id selalu ada, tidak pernah kosong."""
    hasil = {"household_id": f"eq.{household_id}"}
    if type is not None:
        hasil["type"] = f"eq.{type}"
    if is_active is not None:
        hasil["is_active"] = f"eq.{str(is_active).lower()}"
    return hasil


def _tautan(household_id: UUID, type: str | None, is_active: bool | None, sort: str) -> dict:
    """Penyaring dalam bentuk parameter API (bukan sintaks PostgREST).

    Dipakai untuk links paginasi supaya tautan bisa diikuti klien apa adanya,
    misalnya /api/v1/accounts?household_id=...&type=bank&page=2.
    """
    hasil = {"household_id": str(household_id)}
    if type is not None:
        hasil["type"] = type
    if is_active is not None:
        hasil["is_active"] = str(is_active).lower()
    if sort != SORT_BAWAAN:
        hasil["sort"] = sort
    return hasil


async def _ambil(account_id: UUID, token: str) -> dict | None:
    """Satu baris dompet yang terlihat oleh pengguna (RLS), atau None."""
    baris = await rest_select("accounts", {"id": f"eq.{account_id}", "select": KOLOM, "limit": 1}, token)
    return baris[0] if baris else None


def _galat_konflik(galat: KonflikData, pesan_unik: str, pesan_kunci_asing: str) -> AppError:
    """Pilih pesan 409 berdasarkan kode Postgres (Bab 4.3)."""
    return conflict(pesan_kunci_asing if galat.kode_postgres == KODE_KUNCI_ASING else pesan_unik)


# -------------------------------------------------------------------- endpoint
@router.get("")
async def daftar_dompet(
    request: Request,
    household_id: UUID,
    type: AccountType | None = Query(default=None, description="Penyaring jenis dompet."),
    is_active: bool | None = Query(default=None, description="Penyaring dompet aktif atau diarsipkan."),
    sort: str = Query(default=SORT_BAWAAN, description="kolom:asc atau kolom:desc."),
    params: PageParams = Depends(page_params),
    token: str = Depends(get_access_token),
) -> dict:
    """Daftar dompet satu rumah tangga. household_id wajib dikirim."""
    urutan = _urutan(sort)
    penyaring = _penyaring(household_id, type, is_active)
    total = await rest_hitung("accounts", penyaring, token)
    baris = await rest_select(
        "accounts",
        {**penyaring, "select": KOLOM, "order": urutan, "limit": params.per_page, "offset": params.offset},
        token,
    )
    # links membawa penyaring supaya tidak hilang saat pindah halaman
    return list_response(baris, params, total, request.url.path, _tautan(household_id, type, is_active, sort))


@router.get("/{account_id}")
async def detail_dompet(account_id: UUID, token: str = Depends(get_access_token)) -> dict:
    """Satu dompet. 404 bila tidak ada atau bukan milik rumah tangga pengguna."""
    baris = await _ambil(account_id, token)
    if baris is None:
        raise not_found("Dompet tidak ditemukan.")
    return {"data": baris}


@router.post("", status_code=status.HTTP_201_CREATED)
async def tambah_dompet(
    payload: AccountCreate,
    user: dict = Depends(get_current_user),
    token: str = Depends(get_access_token),
) -> dict:
    """Tambah dompet baru. Hanya ayah dan ibu."""
    await wajib_penulis(token, str(payload.household_id), user.get("sub"))
    try:
        baris = await rest_insert("accounts", payload.model_dump(mode="json"), token)
    except KonflikData as galat:
        raise _galat_konflik(galat, "Nama dompet sudah dipakai.", "Rumah tangga tujuan tidak ditemukan.") from galat
    return {"data": baris[0] if baris else None}


@router.patch("/{account_id}")
async def ubah_dompet(
    account_id: UUID,
    payload: AccountUpdate,
    user: dict = Depends(get_current_user),
    token: str = Depends(get_access_token),
) -> dict:
    """Ubah sebagian kolom dompet. Hanya ayah dan ibu."""
    baris = await _ambil(account_id, token)
    if baris is None:
        raise not_found("Dompet tidak ditemukan.")
    await wajib_penulis(token, baris["household_id"], user.get("sub"))

    perubahan = payload.model_dump(exclude_none=True, mode="json")
    if not perubahan:
        raise AppError(400, "VALIDATION_ERROR", "Tidak ada kolom yang diubah.")

    try:
        hasil = await rest_patch("accounts", {"id": f"eq.{account_id}"}, perubahan, token)
    except KonflikData as galat:
        raise _galat_konflik(galat, "Nama dompet sudah dipakai.", "Rumah tangga tujuan tidak ditemukan.") from galat
    if not hasil:
        raise not_found("Dompet tidak ditemukan.")
    return {"data": hasil[0]}


@router.delete("/{account_id}")
async def hapus_dompet(
    account_id: UUID,
    user: dict = Depends(get_current_user),
    token: str = Depends(get_access_token),
) -> dict:
    """Hapus dompet. Dompet yang masih dipakai transaksi ditolak 409 (RESTRICT)."""
    baris = await _ambil(account_id, token)
    if baris is None:
        raise not_found("Dompet tidak ditemukan.")
    await wajib_penulis(token, baris["household_id"], user.get("sub"))

    try:
        hasil = await rest_delete("accounts", {"id": f"eq.{account_id}"}, token)
    except KonflikData as galat:
        raise _galat_konflik(galat, "Nama dompet sudah dipakai.", "Dompet masih dipakai transaksi.") from galat
    if not hasil:
        raise not_found("Dompet tidak ditemukan.")
    return {"data": None, "message": "baris dihapus"}
