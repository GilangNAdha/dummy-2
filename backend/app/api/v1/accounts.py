# router /accounts: terima permintaan, panggil service, kembalikan respons
# Penulis: Gilang Nur Adha
from fastapi import APIRouter, Depends, Query, Request

from app.core.deps import get_access_token, get_current_user
from app.core.pagination import PageParams, list_response, page_params
from app.schemas.account import DompetBaru, DompetUbah, JenisDompet
from app.services import account_service as layanan

router = APIRouter(prefix="/accounts", tags=["dompet"])


@router.get("")
async def daftar_dompet(
    request: Request,
    household_id: str,
    type: JenisDompet | None = None,
    is_active: bool | None = None,
    sort: str | None = Query(default=None, description="Contoh name:asc. Bawaan created_at:desc."),
    params: PageParams = Depends(page_params),
    user: dict = Depends(get_current_user),
    token: str = Depends(get_access_token),
) -> dict:
    """Daftar dompet satu rumah tangga beserta current_balance. Boleh dibaca semua anggota."""
    baris, total = await layanan.daftar(token, user, household_id, type, is_active, sort, params.per_page, params.offset)
    extra = {k: v for k, v in {"household_id": household_id, "type": type, "sort": sort}.items() if v}
    if is_active is not None:
        extra["is_active"] = str(is_active).lower()
    return list_response(baris, params, total, request.url.path, extra)


@router.get("/{account_id}")
async def detail_dompet(account_id: str, user: dict = Depends(get_current_user), token: str = Depends(get_access_token)) -> dict:
    return {"data": await layanan.detail(token, user, account_id)}


@router.post("", status_code=201)
async def tambah_dompet(payload: DompetBaru, user: dict = Depends(get_current_user), token: str = Depends(get_access_token)) -> dict:
    """Tambah dompet, khusus Ayah dan Ibu."""
    return {"data": await layanan.tambah(token, user, payload.model_dump())}


@router.patch("/{account_id}")
async def ubah_dompet(
    account_id: str,
    payload: DompetUbah,
    user: dict = Depends(get_current_user),
    token: str = Depends(get_access_token),
) -> dict:
    """Ubah sebagian kolom. Arsipkan dengan is_active=false."""
    return {"data": await layanan.ubah(token, user, account_id, payload.model_dump(exclude_unset=True))}


@router.delete("/{account_id}")
async def hapus_dompet(account_id: str, user: dict = Depends(get_current_user), token: str = Depends(get_access_token)) -> dict:
    """Hapus dompet. Ditolak 409 bila masih dirujuk transaksi atau setoran tujuan."""
    await layanan.hapus(token, user, account_id)
    return {"data": None, "message": "baris dihapus"}
