# pemeriksaan peran pada satu rumah tangga
#
# Peran disimpan di tabel household_members, bukan di dalam token, sehingga
# perubahan peran langsung berlaku (panduan kerja langkah 6).
#
# Catatan SESUAIKAN: panduan kerja menyebut dependensi ``require_role`` milik
# Chandra yang akan dipasang di core/deps.py. Berkas itu belum ada di repositori,
# jadi pemeriksaan peran ditaruh di berkas tersendiri ini supaya router dompet
# dan kategori tidak bergantung pada berkas milik anggota lain. Bila
# ``require_role`` sudah tersedia, isi berkas ini bisa dipindahkan ke sana
# tanpa mengubah bentuk pemeriksaan.
from app.core.errors import forbidden
from app.core.supabase_client import rest_select

# Bab 3.4: dompet dan kategori boleh dibaca semua anggota, tetapi hanya
# ayah dan ibu yang boleh menambah, mengubah, dan menghapus.
PERAN_TULIS = ("ayah", "ibu")


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


async def wajib_penulis(token: str, household_id: str, user_id: str | None) -> str:
    """Pastikan pengguna anggota rumah tangga dengan peran yang boleh menulis.

    Ini lapisan pertama (pesan galat yang jelas di FastAPI). Lapisan terakhir
    tetap kebijakan RLS di basis data, karena setiap permintaan ke PostgREST
    membawa token asli pengguna.
    """
    peran = await peran_pengguna(token, household_id, user_id)
    if peran is None:
        raise forbidden("Kamu bukan anggota rumah tangga itu.")
    if peran not in PERAN_TULIS:
        raise forbidden("Hanya Ayah dan Ibu yang boleh mengubah dompet dan kategori.")
    return peran
