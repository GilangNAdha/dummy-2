# router /categories: terima permintaan, panggil service, kembalikan respons
# Penulis: Gilang Nur Adha
from fastapi import APIRouter, Depends, Query, Request

from app.core.deps import get_access_token, get_current_user
from app.core.pagination import PageParams, list_response, page_params
from app.schemas.category import JenisKategori, KategoriBaru, KategoriUbah
from app.services import category_service as layanan

router = APIRouter(prefix="/categories", tags=["kategori"])


@router.get("")
async def daftar_kategori(
    request: Request,
    household_id: str,
    kind: JenisKategori | None = None,
    is_archived: bool | None = None,
    sort: str | None = Query(default=None, description="Contoh name:asc. Bawaan created_at:desc."),
    params: PageParams = Depends(page_params),
    user: dict = Depends(get_current_user),
    token: str = Depends(get_access_token),
) -> dict:
    """Kategori sistem ditambah kategori milik rumah tangga."""
    baris, total = await layanan.daftar(token, user, household_id, kind, is_archived, sort, params.per_page, params.offset)
    extra = {k: v for k, v in {"household_id": household_id, "kind": kind, "sort": sort}.items() if v}
    if is_archived is not None:
        extra["is_archived"] = str(is_archived).lower()
    return list_response(baris, params, total, request.url.path, extra)


@router.get("/{category_id}")
async def detail_kategori(category_id: str, user: dict = Depends(get_current_user), token: str = Depends(get_access_token)) -> dict:
    return {"data": await layanan.detail(token, user, category_id)}


@router.post("", status_code=201)
async def tambah_kategori(payload: KategoriBaru, user: dict = Depends(get_current_user), token: str = Depends(get_access_token)) -> dict:
    """Tambah kategori keluarga (is_system selalu false), khusus Ayah dan Ibu."""
    return {"data": await layanan.tambah(token, user, payload.model_dump())}


@router.patch("/{category_id}")
async def ubah_kategori(
    category_id: str,
    payload: KategoriUbah,
    user: dict = Depends(get_current_user),
    token: str = Depends(get_access_token),
) -> dict:
    return {"data": await layanan.ubah(token, user, category_id, payload.model_dump(exclude_unset=True))}


@router.delete("/{category_id}")
async def hapus_kategori(category_id: str, user: dict = Depends(get_current_user), token: str = Depends(get_access_token)) -> dict:
    """Kategori sistem 403. Kategori yang dipakai transaksi 409, arsipkan dengan is_archived=true."""
    await layanan.hapus(token, user, category_id)
    return {"data": None, "message": "baris dihapus"}
