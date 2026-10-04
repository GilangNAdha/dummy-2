# endpoint dompet (rekening bank, tunai, e-wallet)
# Penulis: Gilang Nur Adha
from typing import Literal

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, ConfigDict, Field, StrictInt

from app.core.deps import get_access_token, get_current_user
from app.core.errors import AppError, conflict, not_found
from app.core.pagination import PageParams, list_response, page_params
from app.core.peran import wajib_anggota, wajib_penulis
from app.core.supabase_client import rest_delete, rest_hitung, rest_insert, rest_patch, rest_select

router = APIRouter(prefix="/accounts", tags=["dompet"])

TABEL = "accounts"
KOLOM = "id,household_id,name,type,icon,opening_balance,is_archived,created_at,updated_at"
JenisDompet = Literal["bank", "cash", "ewallet"]


class DompetBaru(BaseModel):
    model_config = ConfigDict(extra="forbid")

    household_id: str = Field(min_length=1)
    name: str = Field(min_length=1, max_length=60)
    type: JenisDompet = "cash"
    icon: str | None = Field(default=None, max_length=8)
    opening_balance: StrictInt = Field(default=0, ge=0)


class DompetUbah(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=60)
    type: JenisDompet | None = None
    icon: str | None = Field(default=None, max_length=8)
    opening_balance: StrictInt | None = Field(default=None, ge=0)
    is_archived: bool | None = None


async def _ambil(token: str, account_id: str) -> dict:
    baris = await rest_select(TABEL, {"id": f"eq.{account_id}", "select": KOLOM, "limit": 1}, token)
    if not baris:
        raise not_found("Dompet tidak ditemukan.")
    return baris[0]


async def _cek_nama_ganda(token: str, household_id: str, name: str, kecuali: str | None = None) -> None:
    params = {"household_id": f"eq.{household_id}", "name": f"eq.{name}", "select": "id", "limit": 1}
    if kecuali:
        params["id"] = f"neq.{kecuali}"
    if await rest_select(TABEL, params, token):
        raise conflict("Nama dompet sudah dipakai di rumah tangga ini.")


@router.get("")
async def daftar_dompet(
    request: Request,
    household_id: str,
    termasuk_arsip: bool = Query(default=False, alias="include_archived"),
    params: PageParams = Depends(page_params),
    user: dict = Depends(get_current_user),
    token: str = Depends(get_access_token),
) -> dict:
    """Daftar dompet satu rumah tangga, boleh dibaca semua anggota."""
    await wajib_anggota(token, household_id, user)
    saring = {"household_id": f"eq.{household_id}"}
    if not termasuk_arsip:
        saring["is_archived"] = "eq.false"
    query = {**saring, "select": KOLOM, "order": "created_at.asc", "limit": params.per_page, "offset": params.offset}
    baris = await rest_select(TABEL, query, token)
    total = await rest_hitung(TABEL, saring, token)
    extra = {"household_id": household_id}
    if termasuk_arsip:
        extra["include_archived"] = "true"
    return list_response(baris, params, total, request.url.path, extra)


@router.get("/{account_id}")
async def detail_dompet(account_id: str, user: dict = Depends(get_current_user), token: str = Depends(get_access_token)) -> dict:
    dompet = await _ambil(token, account_id)
    await wajib_anggota(token, dompet["household_id"], user)
    return {"data": dompet}


@router.post("", status_code=201)
async def tambah_dompet(payload: DompetBaru, user: dict = Depends(get_current_user), token: str = Depends(get_access_token)) -> dict:
    """Tambah dompet baru, khusus Ayah dan Ibu."""
    await wajib_penulis(token, payload.household_id, user)
    data = payload.model_dump()
    data["name"] = data["name"].strip()
    await _cek_nama_ganda(token, payload.household_id, data["name"])
    baris = await rest_insert(TABEL, data, token)
    return {"data": baris[0] if baris else data}


@router.patch("/{account_id}")
async def ubah_dompet(
    account_id: str,
    payload: DompetUbah,
    user: dict = Depends(get_current_user),
    token: str = Depends(get_access_token),
) -> dict:
    perubahan = payload.model_dump(exclude_none=True)
    if not perubahan:
        raise AppError(400, "VALIDATION_ERROR", "Tidak ada kolom yang diubah.")
    dompet = await _ambil(token, account_id)
    await wajib_penulis(token, dompet["household_id"], user)
    if "name" in perubahan:
        perubahan["name"] = perubahan["name"].strip()
        await _cek_nama_ganda(token, dompet["household_id"], perubahan["name"], kecuali=account_id)
    baris = await rest_patch(TABEL, {"id": f"eq.{account_id}"}, perubahan, token)
    if not baris:
        raise not_found("Dompet tidak ditemukan.")
    return {"data": baris[0]}


@router.delete("/{account_id}", status_code=204)
async def hapus_dompet(account_id: str, user: dict = Depends(get_current_user), token: str = Depends(get_access_token)) -> None:
    dompet = await _ambil(token, account_id)
    await wajib_penulis(token, dompet["household_id"], user)
    await rest_delete(TABEL, {"id": f"eq.{account_id}"}, token)
