# endpoint kategori (categories)
#
# Pola mengikuti app/api/v1/profiles.py dan accounts.py: router tipis, tanpa
# perhitungan, akses data lewat core/supabase_client.py dengan token pengguna
# sehingga kebijakan RLS berlaku sebagai pengguna itu.
#
# Aturan khusus kategori (panduan kerja langkah 5):
#   - kategori sistem (household_id kosong, is_system true) terbaca semua
#     rumah tangga, tetapi tidak bisa diubah atau dihapus siapa pun lewat API
#   - server selalu memaksa is_system = false pada POST; is_system dari klien
#     ditolak 400 oleh skema (extra="forbid")
#   - kategori terarsip tetap muncul di GET kecuali diminta sebaliknya,
#     karena laporan lama membutuhkannya
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from pydantic import BaseModel, ConfigDict, Field

from app.core.deps import get_access_token, get_current_user
from app.core.errors import AppError, conflict, forbidden, not_found
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

router = APIRouter(prefix="/categories", tags=["kategori"])

CategoryKind = Literal["income", "expense"]
WARNA = r"^#[0-9A-Fa-f]{6}$"

KOLOM = "id,household_id,name,kind,icon,color,is_system,is_archived,created_at,updated_at"
SORT_BOLEH = ("created_at", "name", "kind")
SORT_BAWAAN = "created_at:desc"


# ----------------------------------------------------------------- skema Pydantic
class _Dasar(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")


class CategoryCreate(_Dasar):
    household_id: UUID
    name: str = Field(min_length=1, max_length=80)
    kind: CategoryKind
    icon: str | None = Field(default=None, max_length=8)
    color: str = Field(default="#94A3B8", pattern=WARNA)
    is_archived: bool = False
    # is_system tidak diterima dari klien; server memaksa false


class CategoryUpdate(_Dasar):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    kind: CategoryKind | None = None
    icon: str | None = Field(default=None, max_length=8)
    color: str | None = Field(default=None, pattern=WARNA)
    is_archived: bool | None = None


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


def _penyaring(
    household_id: UUID,
    kind: str | None,
    is_archived: bool | None,
    is_system: bool | None,
) -> dict:
    """Penyaring PostgREST: kategori rumah tangga DAN kategori sistem.

    Bentuk or=(household_id.eq.{id},household_id.is.null) membuat kategori
    sistem ikut terbaca oleh semua rumah tangga.
    """
    hasil = {"or": f"(household_id.eq.{household_id},household_id.is.null)"}
    if kind is not None:
        hasil["kind"] = f"eq.{kind}"
    if is_archived is not None:
        hasil["is_archived"] = f"eq.{str(is_archived).lower()}"
    if is_system is not None:
        hasil["is_system"] = f"eq.{str(is_system).lower()}"
    return hasil


def _tautan(
    household_id: UUID,
    kind: str | None,
    is_archived: bool | None,
    is_system: bool | None,
    sort: str,
) -> dict:
    """Penyaring dalam bentuk parameter API (bukan sintaks PostgREST).

    Dipakai untuk links paginasi supaya tautan bisa diikuti klien apa adanya,
    misalnya /api/v1/categories?household_id=...&kind=expense&page=2.
    """
    hasil = {"household_id": str(household_id)}
    if kind is not None:
        hasil["kind"] = kind
    if is_archived is not None:
        hasil["is_archived"] = str(is_archived).lower()
    if is_system is not None:
        hasil["is_system"] = str(is_system).lower()
    if sort != SORT_BAWAAN:
        hasil["sort"] = sort
    return hasil


async def _ambil(category_id: UUID, token: str) -> dict | None:
    """Satu baris kategori yang terlihat pengguna (milik rumah tangga atau sistem)."""
    baris = await rest_select("categories", {"id": f"eq.{category_id}", "select": KOLOM, "limit": 1}, token)
    return baris[0] if baris else None


async def _nama_terpakai(token: str, household_id: UUID, nama: str, kecuali_id: UUID | None = None) -> bool:
    """Nama sudah dipakai di rumah tangga itu ATAU oleh kategori sistem.

    Indeks unik rumah tangga tidak mencakup kategori sistem, jadi pemeriksaan
    ini dilakukan di router (panduan kerja langkah 5.2). Kategori sistem hanya
    terbaca, tidak pernah berubah, sehingga aman sebagai acuan nama.
    """
    penyaring = {
        "name": f"eq.{nama}",
        "or": f"(household_id.eq.{household_id},household_id.is.null)",
        "select": "id",
        "limit": 1,
    }
    if kecuali_id is not None:
        penyaring["id"] = f"neq.{kecuali_id}"
    baris = await rest_select("categories", penyaring, token)
    return bool(baris)


def _galat_konflik(galat: KonflikData, pesan_unik: str) -> AppError:
    """409 dari basis data; kategori memakai pesan sama untuk semua penyebab."""
    return conflict(pesan_unik)


# -------------------------------------------------------------------- endpoint
@router.get("")
async def daftar_kategori(
    request: Request,
    household_id: UUID,
    kind: CategoryKind | None = Query(default=None, description="Penyaring jenis kategori."),
    is_archived: bool | None = Query(default=None, description="Penyaring kategori terarsip."),
    is_system: bool | None = Query(default=None, description="Penyaring kategori sistem."),
    sort: str = Query(default=SORT_BAWAAN, description="kolom:asc atau kolom:desc."),
    params: PageParams = Depends(page_params),
    token: str = Depends(get_access_token),
) -> dict:
    """Daftar kategori rumah tangga pengguna beserta kategori sistem."""
    urutan = _urutan(sort)
    penyaring = _penyaring(household_id, kind, is_archived, is_system)
    total = await rest_hitung("categories", penyaring, token)
    baris = await rest_select(
        "categories",
        {**penyaring, "select": KOLOM, "order": urutan, "limit": params.per_page, "offset": params.offset},
        token,
    )
    return list_response(
        baris, params, total, request.url.path, _tautan(household_id, kind, is_archived, is_system, sort)
    )


@router.get("/{category_id}")
async def detail_kategori(category_id: UUID, token: str = Depends(get_access_token)) -> dict:
    """Satu kategori. Kategori sistem boleh dibaca semua rumah tangga."""
    baris = await _ambil(category_id, token)
    if baris is None:
        raise not_found("Kategori tidak ditemukan.")
    return {"data": baris}


@router.post("", status_code=status.HTTP_201_CREATED)
async def tambah_kategori(
    payload: CategoryCreate,
    user: dict = Depends(get_current_user),
    token: str = Depends(get_access_token),
) -> dict:
    """Tambah kategori rumah tangga. Hanya ayah dan ibu, is_system selalu false."""
    await wajib_penulis(token, str(payload.household_id), user.get("sub"))
    if await _nama_terpakai(token, payload.household_id, payload.name):
        raise conflict("Nama kategori sudah dipakai.")

    isi = payload.model_dump(mode="json")
    isi["is_system"] = False  # server yang memaksa, bukan klien
    try:
        baris = await rest_insert("categories", isi, token)
    except KonflikData as galat:
        raise _galat_konflik(galat, "Nama kategori sudah dipakai.") from galat
    return {"data": baris[0] if baris else None}


@router.patch("/{category_id}")
async def ubah_kategori(
    category_id: UUID,
    payload: CategoryUpdate,
    user: dict = Depends(get_current_user),
    token: str = Depends(get_access_token),
) -> dict:
    """Ubah sebagian kolom kategori. Kategori sistem ditolak 403."""
    baris = await _ambil(category_id, token)
    if baris is None:
        raise not_found("Kategori tidak ditemukan.")
    if baris.get("is_system"):
        raise forbidden("Kategori sistem tidak boleh diubah.")
    await wajib_penulis(token, baris["household_id"], user.get("sub"))

    perubahan = payload.model_dump(exclude_none=True, mode="json")
    if not perubahan:
        raise AppError(400, "VALIDATION_ERROR", "Tidak ada kolom yang diubah.")
    if "name" in perubahan and await _nama_terpakai(token, baris["household_id"], perubahan["name"], category_id):
        raise conflict("Nama kategori sudah dipakai.")

    try:
        hasil = await rest_patch("categories", {"id": f"eq.{category_id}"}, perubahan, token)
    except KonflikData as galat:
        raise _galat_konflik(galat, "Nama kategori sudah dipakai.") from galat
    if not hasil:
        raise not_found("Kategori tidak ditemukan.")
    return {"data": hasil[0]}


@router.delete("/{category_id}")
async def hapus_kategori(
    category_id: UUID,
    user: dict = Depends(get_current_user),
    token: str = Depends(get_access_token),
) -> dict:
    """Hapus kategori rumah tangga. Kategori sistem ditolak 403.

    Akibat penghapusan (Bab 2.5): transaksi terkait menjadi tanpa kategori
    (SET NULL) dan anggaran terkait ikut terhapus (CASCADE). Karena itu
    antarmuka disarankan memakai pengarsipan (is_archived) alih-alih menghapus.
    """
    baris = await _ambil(category_id, token)
    if baris is None:
        raise not_found("Kategori tidak ditemukan.")
    if baris.get("is_system"):
        raise forbidden("Kategori sistem tidak boleh dihapus.")
    await wajib_penulis(token, baris["household_id"], user.get("sub"))

    try:
        hasil = await rest_delete("categories", {"id": f"eq.{category_id}"}, token)
    except KonflikData as galat:
        raise _galat_konflik(galat, "Kategori masih dipakai data lain.") from galat
    if not hasil:
        raise not_found("Kategori tidak ditemukan.")
    return {"data": None, "message": "baris dihapus"}
