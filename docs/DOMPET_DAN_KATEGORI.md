# Dompet dan Kategori

Penanggung jawab: **Gilang Nur Adha**

Bagian ini menambahkan tabel, aturan akses, dan endpoint API untuk **dompet** (`accounts`) dan **kategori** (`categories`).

## Berkas

| Berkas | Isi |
| --- | --- |
| `backend/supabase/migrations/0004_accounts.sql` | tabel `accounts`, enum `account_type`, RLS |
| `backend/supabase/migrations/0005_categories.sql` | tabel `categories`, enum `category_kind`, RLS, 8 kategori sistem |
| `backend/app/core/peran.py` | cek peran anggota (anggota / penulis) |
| `backend/app/api/v1/accounts.py` | endpoint `/api/v1/accounts` |
| `backend/app/api/v1/categories.py` | endpoint `/api/v1/categories` |
| `backend/tests/test_dompet_kategori.py` | pengujian |
| `backend/app/main.py` | hanya 3 baris: impor dan pemasangan router |

## Tabel

**accounts**: `id`, `household_id`, `name` (unik per rumah tangga), `type` (`bank` / `cash` / `ewallet`), `icon`, `opening_balance` (bilangan bulat Rupiah, ≥ 0), `is_archived`, `created_at`, `updated_at`.
Tidak ada nomor rekening atau kredensial bank.

**categories**: `id`, `household_id` (NULL = kategori sistem), `name`, `kind` (`income` / `expense`), `icon`, `color` (`#RRGGBB`), `parent_id`, `is_system`, `is_archived`, `created_at`, `updated_at`.
Delapan kategori sistem diisi otomatis, sama dengan `src/data/mockData.js`.

## Hak akses (dua lapis: API + RLS)

| Aksi | Ayah | Ibu | Anak | Bukan anggota |
| --- | --- | --- | --- | --- |
| Baca dompet / kategori | ✅ | ✅ | ✅ | ❌ 403 |
| Tambah / ubah / hapus | ✅ | ✅ | ❌ 403 | ❌ 403 |
| Ubah / hapus kategori sistem | ❌ 403 | ❌ 403 | ❌ 403 | ❌ 403 |

## Endpoint

Semua butuh header `Authorization: Bearer <token Supabase>`.

| Metode | Jalur | Keterangan |
| --- | --- | --- |
| GET | `/api/v1/accounts?household_id=...` | daftar dompet (`page`, `per_page`, `include_archived`) |
| GET | `/api/v1/accounts/{id}` | detail dompet |
| POST | `/api/v1/accounts` | tambah dompet |
| PATCH | `/api/v1/accounts/{id}` | ubah / arsipkan dompet |
| DELETE | `/api/v1/accounts/{id}` | hapus dompet (204) |
| GET | `/api/v1/categories?household_id=...` | kategori sistem + keluarga (`kind`, `page`, `per_page`, `include_archived`) |
| GET | `/api/v1/categories/{id}` | detail kategori |
| POST | `/api/v1/categories` | tambah kategori keluarga |
| PATCH | `/api/v1/categories/{id}` | ubah kategori keluarga |
| DELETE | `/api/v1/categories/{id}` | hapus kategori keluarga (204) |

Contoh:

```http
POST /api/v1/accounts
{ "household_id": "<uuid>", "name": "GoPay", "type": "ewallet", "icon": "🟢", "opening_balance": 320000 }

POST /api/v1/categories
{ "household_id": "<uuid>", "name": "Arisan", "kind": "expense", "icon": "🎁", "color": "#F59E0B" }
```

Daftar dibalas dalam bentuk `{data, meta, links}`, galat dalam bentuk `{error: {code, message, details, request_id}}`.

| Kode | Arti |
| --- | --- |
| 400 `VALIDATION_ERROR` | isi salah: uang pecahan/negatif, jenis tak dikenal, warna salah, kolom asing |
| 401 `UNAUTHENTICATED` | token tidak ada / tidak sah |
| 403 `FORBIDDEN` | bukan anggota, peran Anak, atau kategori sistem |
| 404 `NOT_FOUND` | data tidak ada |
| 409 `CONFLICT` | nama sudah dipakai di rumah tangga yang sama |

## Menjalankan

```bash
# migrasi (urutan nomor file, setelah 0001-0003)
supabase db push

# uji
cd backend
pip install -r requirements.txt
pytest -q
```

## Catatan untuk tim

- `0005` memakai fungsi `public.set_updated_at()` yang dibuat di `0004`.
- Saldo berjalan dompet belum dihitung; menunggu tabel `transactions` (migrasi 0006/0007).
- Integrasi frontend (`src/API/getData.js`) belum diubah agar mode demo localStorage tetap berjalan.
