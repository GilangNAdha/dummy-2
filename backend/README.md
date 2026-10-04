# Backend KeluargaFin

Layanan FastAPI di atas Supabase Postgres. Seluruh aturan bisnis berada di sini, frontend hanya menampilkan.

## Menjalankan

```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Atau lewat Docker:

```
docker compose up
```

Dokumentasi otomatis tersedia di `/docs`, pemeriksaan kesehatan di `/health`.

## Variabel lingkungan

Salin `.env.example` menjadi `.env` lalu isi nilainya.

| Nama | Isi |
| --- | --- |
| SUPABASE_URL | alamat proyek Supabase |
| SUPABASE_ANON_KEY | kunci anon untuk pemakaian di klien |
| SUPABASE_SERVICE_ROLE_KEY | kunci server, hanya untuk layanan ini |
| SUPABASE_JWKS_URL | alamat kunci publik untuk memeriksa token |
| SUPABASE_JWT_SECRET | hanya untuk pengembangan lokal, tanda tangan HS256 |
| CORS_ORIGINS | daftar asal yang diizinkan, dipisah koma |

## Struktur

```
app/main.py             titik masuk layanan
app/core/config.py      pembacaan variabel lingkungan
app/core/errors.py      bentuk error standar
app/core/pagination.py  fungsi bantu paginasi, dipakai semua router
app/core/supabase_client.py  akses PostgREST
app/core/deps.py        pemeriksaan token Supabase
app/api/v1              router per sumber daya
supabase/migrations     berkas migrasi
tests                   pengujian
```

## Pengujian

```
pytest -q
```
