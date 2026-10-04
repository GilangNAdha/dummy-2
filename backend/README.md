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
app/core/peran.py       pemeriksaan peran ayah dan ibu (pengganti sementara require_role)
app/api/v1              router per sumber daya
supabase/migrations     berkas migrasi
supabase/seed.sql       data contoh, hanya untuk pengembangan dan pengujian
tests                   pengujian
tests/koleksi           koleksi permintaan uji (berkas .http)
```

## Endpoint

| Sumber daya | Endpoint | Keterangan |
| --- | --- | --- |
| Profil | `GET/PATCH /api/v1/profiles/me` | Profil milik pemilik token |
| Dompet | `GET/POST /api/v1/accounts`, `GET/PATCH/DELETE /api/v1/accounts/{id}` | Hanya ayah dan ibu yang boleh menulis |
| Kategori | `GET/POST /api/v1/categories`, `GET/PATCH/DELETE /api/v1/categories/{id}` | Kategori sistem terbaca semua rumah tangga dan tidak bisa diubah |
| Ringkasan dan laporan | `GET /api/v1/dashboard/summary`, `/reports/cashflow`, `/reports/categories`, `/reports/members`, `/reports/export.csv` | Hanya ayah dan ibu |

Setiap router memakai token pengguna untuk memanggil PostgREST, sehingga kebijakan
RLS berlaku sebagai pengguna itu. Daftar memakai bentuk `{data, meta, links}`,
galat memakai bentuk `{error: {code, message, details, request_id}}`.

## Pengujian

```
pytest -q
```
