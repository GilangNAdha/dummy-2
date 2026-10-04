# endpoint kategori pemasukan dan pengeluaran
# Penulis: Gilang Nur Adha
from typing import Literal

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, ConfigDict, Field

from app.core.deps import get_access_token, get_current_user
from app.core.errors import AppError, conflict, forbidden, not_found
from app.core.pagination import PageParams, list_response, page_params
from app.core.peran import wajib_anggota, wajib_penulis
from app.core.supabase_client import rest_delete, rest_hitung, rest_insert, rest_patch, rest_select

router = APIRouter(prefix="/categories", tags=["kategori"])

TABEL = "categories"
KOLOM = "id,household_id,name,kind,icon,color,parent_id,is_system,is_archived,created_at,updated_at"
POLA_WARNA = r"^#[0-9A-Fa-f]{6}$"
JenisKategori = Literal["income", "expense"]


class KategoriBaru(BaseModel):
    model_config = ConfigDict(extra="forbid")

    household_id: str = Field(min_length=1)
    name: str = Field(min_length=1, max_length=60)
    kind: JenisKategori = "expense"
    icon: str | None = Field(default=None, max_length=8)
    color: str = Field(default="#94A3B8", pattern=POLA_WARNA)
    parent_id: str | None = None


class KategoriUbah(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=60)
    kind: JenisKategori | None = None
    icon: str | None = Field(default=None, max_length=8)
    color: str | None = Field(default=None, pattern=POLA_WARNA)
    parent_id: str | None = None
    is_archived: bool | None = None


async def _ambil(token: str, category_id: str) -> dict:
    baris = await rest_select(TABEL, {"id": f"eq.{category_id}", "select": KOLOM, "limit": 1}, token)
    if not baris:
        raise not_found("Kategori tidak ditemukan.")
    return baris[0]


async def _ambil_keluarga(token: str, category_id: str, user: dict) -> dict:
    """Kategori milik keluarga yang boleh ditulis; kategori sistem selalu ditolak 403."""
    kategori = await _ambil(token, category_id)
    if kategori.get("is_system") or not kategori.get("household_id"):
        raise forbidden("Kategori sistem tidak bisa diubah atau dihapus.")
    await wajib_penulis(token, kategori["household_id"], user)
    return kategori


async def _cek_nama_ganda(token: str, household_id: str, name: str, kecuali: str | None = None) -> None:
    params = {"household_id": f"eq.{household_id}", "name": f"eq.{name}", "select": "id", "limit": 1}
    if kecuali:
        params["id"] = f"neq.{kecuali}"
    if await rest_select(TABEL, params, token):
        raise conflict("Nama kategori sudah dipakai di rumah tangga ini.")


async def _cek_induk(token: str, household_id: str, parent_id: str, diri: str | None = None) -> None:
    if diri and parent_id == diri:
        raise AppError(400, "VALIDATION_ERROR", "Kategori tidak boleh menjadi induk dirinya sendiri.")
    induk = await _ambil(token, parent_id)
    if induk.get("household_id") not in (None, household_id):
        raise AppError(400, "VALIDATION_ERROR", "Kategori induk harus milik rumah tangga yang sama.")


@router.get("")
async def daftar_kategori(
    request: Request,
    household_id: str,
    kind: JenisKategori | None = None,
    termasuk_arsip: bool = Query(default=False, alias="include_archived"),
    params: PageParams = Depends(page_params),
    user: dict = Depends(get_current_user),
    token: str = Depends(get_access_token),
) -> dict:
    """Kategori sistem ditambah kategori milik rumah tangga."""
    await wajib_anggota(token, household_id, user)
    saring = {"or": f"(household_id.is.null,household_id.eq.{household_id})"}
    if kind:
        saring["kind"] = f"eq.{kind}"
    if not termasuk_arsip:
        saring["is_archived"] = "eq.false"
    query = {**saring, "select": KOLOM, "order": "is_system.desc,name.asc", "limit": params.per_page, "offset": params.offset}
    baris = await rest_select(TABEL, query, token)
    total = await rest_hitung(TABEL, saring, token)
    extra = {"household_id": household_id}
    if kind:
        extra["kind"] = kind
    if termasuk_arsip:
        extra["include_archived"] = "true"
    return list_response(baris, params, total, request.url.path, extra)


@router.get("/{category_id}")
async def detail_kategori(category_id: str, user: dict = Depends(get_current_user), token: str = Depends(get_access_token)) -> dict:
    kategori = await _ambil(token, category_id)
    if kategori.get("household_id"):
        await wajib_anggota(token, kategori["household_id"], user)
    return {"data": kategori}


@router.post("", status_code=201)
async def tambah_kategori(payload: KategoriBaru, user: dict = Depends(get_current_user), token: str = Depends(get_access_token)) -> dict:
    """Tambah kategori keluarga, khusus Ayah dan Ibu."""
    await wajib_penulis(token, payload.household_id, user)
    data = payload.model_dump(exclude_none=True)
    data["name"] = data["name"].strip()
    data["is_system"] = False
    await _cek_nama_ganda(token, payload.household_id, data["name"])
    if payload.parent_id:
        await _cek_induk(token, payload.household_id, payload.parent_id)
    baris = await rest_insert(TABEL, data, token)
    return {"data": baris[0] if baris else data}


@router.patch("/{category_id}")
async def ubah_kategori(
    category_id: str,
    payload: KategoriUbah,
    user: dict = Depends(get_current_user),
    token: str = Depends(get_access_token),
) -> dict:
    perubahan = payload.model_dump(exclude_none=True)
    if not perubahan:
        raise AppError(400, "VALIDATION_ERROR", "Tidak ada kolom yang diubah.")
    kategori = await _ambil_keluarga(token, category_id, user)
    if "name" in perubahan:
        perubahan["name"] = perubahan["name"].strip()
        await _cek_nama_ganda(token, kategori["household_id"], perubahan["name"], kecuali=category_id)
    if "parent_id" in perubahan:
        await _cek_induk(token, kategori["household_id"], perubahan["parent_id"], diri=category_id)
    baris = await rest_patch(TABEL, {"id": f"eq.{category_id}"}, perubahan, token)
    if not baris:
        raise not_found("Kategori tidak ditemukan.")
    return {"data": baris[0]}


@router.delete("/{category_id}", status_code=204)
async def hapus_kategori(category_id: str, user: dict = Depends(get_current_user), token: str = Depends(get_access_token)) -> None:
    await _ambil_keluarga(token, category_id, user)
    await rest_delete(TABEL, {"id": f"eq.{category_id}"}, token)
