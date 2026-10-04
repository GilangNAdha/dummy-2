# akses basis data lewat PostgREST
import httpx

from app.core.config import get_settings
from app.core.errors import AppError

TIMEOUT = 10.0


def _kunci() -> str:
    settings = get_settings()
    return settings.supabase_service_role_key or settings.supabase_anon_key


def _headers(token: str | None = None, prefer: str | None = None) -> dict:
    settings = get_settings()
    kunci = _kunci()
    if not settings.supabase_url or not kunci:
        raise AppError(503, "SUPABASE_UNAVAILABLE", "Data sedang tidak dapat diakses, coba lagi sebentar lagi.")
    headers = {
        "apikey": kunci,
        "Authorization": f"Bearer {token or kunci}",
        "Content-Type": "application/json",
    }
    if prefer:
        headers["Prefer"] = prefer
    return headers


def rest_url(table: str) -> str:
    settings = get_settings()
    return f"{settings.supabase_url.rstrip('/')}/rest/v1/{table}"


# kode galat Postgres yang perlu diterjemahkan menjadi kode API
KODE_UNIK = "23505"         # unique_violation
KODE_KUNCI_ASING = "23503"  # foreign_key_violation
KODE_IZIN = "42501"         # insufficient_privilege (ditolak RLS)


class KonflikData(AppError):
    """Galat 409 dari PostgREST beserta kode Postgres penyebabnya.

    Router memakai ``kode_postgres`` untuk memilih pesan yang tepat, misalnya
    23505 menjadi "Nama dompet sudah dipakai." dan 23503 menjadi "Dompet masih
    dipakai transaksi." (panduan kerja langkah 4.3).
    """

    def __init__(self, kode_postgres: str):
        super().__init__(
            409,
            "CONFLICT",
            "Datanya sudah ada atau masih dipakai data lain.",
            [{"kode_postgres": kode_postgres}],
        )
        self.kode_postgres = kode_postgres


def _kode_postgres(res: httpx.Response) -> str:
    """Kode Postgres dari badan galat PostgREST, misalnya 23505, bila ada."""
    try:
        isi = res.json()
    except Exception:
        return ""
    if isinstance(isi, dict):
        return str(isi.get("code") or "")
    return ""


def _cek(res: httpx.Response, pesan: str = "Gagal mengambil data dari basis data.") -> list:
    kode = _kode_postgres(res)
    if res.status_code in (401, 403) or kode == KODE_IZIN:
        raise AppError(403, "FORBIDDEN", "Kamu tidak punya izin untuk aksi ini pada data itu.")
    if res.status_code == 409 or kode in (KODE_UNIK, KODE_KUNCI_ASING):
        raise KonflikData(kode or str(res.status_code))
    if res.status_code >= 400:
        raise AppError(502, "SUPABASE_ERROR", pesan, [{"status": res.status_code}])
    if not res.content:
        return []
    return res.json()


def _jumlah_dari_range(res: httpx.Response) -> int:
    """Baca jumlah baris dari header Content-Range, bentuknya '0-19/137' atau '*/0'."""
    isi = res.headers.get("content-range", "")
    if "/" in isi:
        ekor = isi.split("/")[-1].strip()
        if ekor.isdigit():
            return int(ekor)
    return 0


async def rest_select(table: str, params: dict, token: str | None = None) -> list:
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        res = await client.get(rest_url(table), params=params, headers=_headers(token))
    return _cek(res)


async def rest_insert(table: str, payload: dict, token: str | None = None) -> list:
    headers = _headers(token, prefer="return=representation")
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        res = await client.post(rest_url(table), json=payload, headers=headers)
    return _cek(res)


async def rest_patch(table: str, params: dict, payload: dict, token: str | None = None) -> list:
    headers = _headers(token, prefer="return=representation")
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        res = await client.patch(rest_url(table), params=params, json=payload, headers=headers)
    return _cek(res)


async def rest_delete(table: str, params: dict, token: str | None = None) -> list:
    headers = _headers(token, prefer="return=representation")
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        res = await client.delete(rest_url(table), params=params, headers=headers)
    return _cek(res)


async def rest_hitung(table: str, params: dict, token: str | None = None) -> int:
    """Jumlah baris yang cocok penyaring, dibaca dari header Content-Range tanpa mengunduh isinya."""
    kirim = {k: v for k, v in params.items() if k not in ("limit", "offset", "order")}
    kirim["limit"] = 1
    headers = _headers(token, prefer="count=exact")
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        res = await client.get(rest_url(table), params=kirim, headers=headers)
    _cek(res)
    return _jumlah_dari_range(res)
