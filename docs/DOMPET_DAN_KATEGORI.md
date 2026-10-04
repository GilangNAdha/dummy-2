# Dompet dan Kategori

Penanggung jawab: **Gilang Nur Adha**
Acuan: Panduan Tugas Gilang Nur Adha (4 Oktober 2026), dokumen perancangan v4.0.

Bagian ini berisi tabel, aturan akses (RLS), endpoint API, dan perhitungan saldo berjalan untuk
**dompet** (`accounts`) dan **kategori** (`categories`).

## 1. Berkas

| Lapisan | Berkas | Isi |
| --- | --- | --- |
| migrasi | `backend/supabase/migrations/0004_accounts.sql` | tabel `accounts`, enum `account_type`, indeks, trigger `updated_at`, RLS |
| migrasi | `backend/supabase/migrations/0005_categories.sql` | tabel `categories`, enum `category_kind`, indeks, RLS, seed 8 kategori sistem |
| seed | `backend/supabase/seed.sql` | 3 dompet contoh (lokal saja) |
| api | `backend/app/api/v1/accounts.py`, `categories.py` | router, tanpa perhitungan |
| schemas | `backend/app/schemas/account.py`, `category.py` | validasi masukan dan bentuk keluaran |
| services | `backend/app/services/account_service.py` | aturan dompet dan `current_balance` |
| services | `backend/app/services/category_service.py` | aturan kategori sistem, nama ganda, kategori terpakai |
| services | `backend/app/services/akses.py` | cek peran (sementara, sampai `require_role` dari Chandra ada) |
| services | `backend/app/services/urutan.py` | `sort=kolom:arah` ke format PostgREST |
| repositories | `backend/app/repositories/accounts.py`, `categories.py`, `anggota.py` | query CRUD, agregasi, penyaringan |
| tests | `backend/tests/test_accounts.py`, `test_categories.py`, `palsu_supabase.py` | pengujian otomatis |
| bukti | `backend/tests/koleksi/` | koleksi permintaan `.http` dan uji RLS SQL |

Berkas tim yang tersentuh: `backend/app/main.py` (3 baris pemasangan router) dan `backend/README.md` (satu bagian tautan).
Berkas `core/*` milik Chandra **tidak diubah**.

## 2. Tabel

**accounts**

| Kolom | Tipe | Catatan |
| --- | --- | --- |
| id | UUID | PK |
| household_id | UUID | FK `households`, `ON DELETE RESTRICT` |
| name | VARCHAR(80) | unik per rumah tangga |
| type | `account_type` | `bank`, `cash`, `ewallet` |
| provider | VARCHAR(60) | opsional, misalnya BCA, GoPay |
| opening_balance | BIGINT | rupiah, default 0, tanpa CHECK |
| is_active | BOOLEAN | `false` = diarsipkan |
| created_at, updated_at | TIMESTAMPTZ | `updated_at` lewat trigger |

Tidak ada kolom saldo berjalan, nomor rekening, nomor kartu, atau PIN.

**categories**

| Kolom | Tipe | Catatan |
| --- | --- | --- |
| id | UUID | PK |
| household_id | UUID | NULL = kategori sistem; FK `households` CASCADE untuk kategori keluarga |
| name | VARCHAR(80) | unik per rumah tangga, nama sistem dijaga indeks parsial |
| kind | `category_kind` | `income`, `expense` |
| icon | VARCHAR(8) | opsional |
| color | CHAR(7) | `#RRGGBB`, default `#94A3B8` (CHECK) |
| is_system | BOOLEAN | wajib sama dengan `household_id IS NULL` (CHECK) |
| is_archived | BOOLEAN | arsip tetap dipakai laporan lama |
| created_at, updated_at | TIMESTAMPTZ | |

Kategori sistem (di migrasi 0005, agar ikut terpasang di produksi):
Makanan dan Minuman, Transportasi, Belanja, Pendidikan, Kesehatan, Tagihan dan Utilitas, Hiburan (pengeluaran) dan Gaji (pemasukan).

## 3. Hak akses (dua lapis: FastAPI + RLS)

| Aksi | Ayah | Ibu | Anak | Rumah tangga lain |
| --- | --- | --- | --- | --- |
| Baca dompet dan kategori | ya | ya | ya | daftar 403, detail 404 |
| Tambah dan ubah | ya | ya | 403 | 404 |
| Hapus dompet | ya | ya, kecuali dompet bersaldo (403) | 403 | 404 |
| Ubah atau hapus kategori sistem | 403 | 403 | 403 | 403 |

Data rumah tangga lain dijawab **404** agar keberadaannya tidak bocor.

## 4. Endpoint

Awalan `/api/v1`, header `Authorization: Bearer <access_token Supabase>`.

| Metode | Jalur | Sukses | Keterangan |
| --- | --- | --- | --- |
| GET | `/accounts?household_id=` | 200 | saring `type`, `is_active`; `sort`, `page`, `per_page` |
| GET | `/accounts/{id}` | 200 | termasuk `current_balance` |
| POST | `/accounts` | 201 | nama ganda 409 |
| PATCH | `/accounts/{id}` | 200 | sebagian kolom, `household_id` tidak bisa diganti |
| DELETE | `/accounts/{id}` | 200 | 409 bila masih dirujuk transaksi atau setoran tujuan |
| GET | `/categories?household_id=` | 200 | sistem + keluarga; saring `kind`, `is_archived`; `sort`, `page`, `per_page` |
| GET | `/categories/{id}` | 200 | |
| POST | `/categories` | 201 | `is_system` selalu `false`, nama ganda 409 |
| PATCH | `/categories/{id}` | 200 | ganti `kind` saat sudah dipakai transaksi 409 |
| DELETE | `/categories/{id}` | 200 | 409 bila dipakai transaksi, arsipkan saja |

- Paginasi: bawaan `page=1`, `per_page=20`, maksimum 100.
- Urutan: `sort=name:asc`; bawaan `created_at:desc`. Kolom tak dikenal 400.
- Daftar: `{data, meta, links}`. Satu objek: `{data}`. Hapus: `{"data": null, "message": "baris dihapus"}`.
- Galat: `{error: {code, message, details, request_id}}` dengan kode 400, 401, 403, 404, 409.

Contoh:

```http
POST /api/v1/accounts
{ "household_id": "<uuid>", "name": "GoPay", "type": "ewallet", "provider": "GoPay", "opening_balance": 320000 }

200 GET /api/v1/accounts?household_id=<uuid>
{ "data": [ { "id": "...", "name": "BCA Utama", "type": "bank", "provider": "BCA",
              "opening_balance": 1000000, "is_active": true, "current_balance": 1250000 } ],
  "meta": { "page": 1, "per_page": 20, "total": 1 }, "links": { "next": null, "prev": null } }
```

## 5. Saldo berjalan `current_balance`

Dihitung di `account_service.hitung_saldo`, tidak disimpan di tabel, frontend hanya menampilkan.

```
current_balance = opening_balance
                + income  (account_id = dompet)
                - expense (account_id = dompet)
                - transfer keluar (account_id = dompet)
                + transfer masuk  (to_account_id = dompet)
```

- Transfer satu baris, bukan pengeluaran; total semua dompet tetap.
- Transaksi dengan `deleted_at` terisi diabaikan.
- Daftar dompet memakai **satu query** transaksi untuk semua dompet di halaman itu, disaring `household_id`.
- Selama tabel `transactions` (migrasi 0006, Apri) belum ada, saldo = `opening_balance`.

## 6. Menjalankan dan menguji

```bash
supabase db reset           # lokal: migrasi + seed.sql
supabase db push            # produksi: migrasi saja (kategori sistem ikut)

cd backend
pip install -r requirements.txt
pytest -q                   # 90 passed (30 lama + 60 baru)
```

Koleksi permintaan: `backend/tests/koleksi/dompet_kategori.http`.

### Bukti uji migrasi dan RLS (PostgreSQL 16 lokal, tiruan skema `auth`)

```bash
psql -f backend/tests/koleksi/rls_prelude.sql -f <migrasi 0001..0005>   # dua kali
cd backend && psql -f tests/koleksi/rls_dompet_kategori.sql
```

Hasil 4 Oktober 2026:

| Pemeriksaan | Hasil |
| --- | --- |
| Migrasi 0001 sampai 0005 dijalankan dua kali | tanpa error |
| Kategori sistem / dompet seed (seed dijalankan dua kali) | 8 / 3, tanpa duplikat |
| RLS aktif, jumlah kebijakan | accounts dan categories true, 4 kebijakan |
| Nama dompet ganda, warna salah, kategori sistem ganda, sistem dengan household | ditolak |
| Hapus rumah tangga yang masih punya dompet | ditolak (RESTRICT) |
| Pengguna rumah tangga lain melihat dompet / kategori | 0 / 8 (hanya kategori sistem) |
| Anak membaca dompet | 3 baris |
| Anak insert dompet dan kategori, update dompet | ditolak RLS, 0 baris berubah |
| Ayah ubah kategori sistem / kategori sendiri | 0 / 1 baris |
| Trigger `updated_at` | berjalan |

Catatan: 0001 memakai `citext` yang tidak ada di PostgreSQL lokal itu, jadi pada uji ini `citext` diganti domain `text`. Di Supabase ekstensi itu tersedia.

## 7. Perlu disepakati di koordinasi Sabtu

1. Delapan nama kategori sistem (usulan di atas, mengikuti contoh dokumen "Makanan dan Minuman", "Tagihan dan Utilitas").
2. Kategori sistem di migrasi 0005, data contoh di `seed.sql`; seed dompet butuh rumah tangga contoh "Keluarga Santoso".
3. Pemilik service saldo: dikerjakan Gilang sesuai tabel potongan, konfirmasi dengan Chandra dan Apri.
4. Akses data tetap PostgREST lewat `httpx` (RLS tetap berlaku); penjumlahan saldo dilakukan di service.
5. DELETE kategori yang dipakai transaksi: 409, arahkan ke arsip.
6. Kategori keluarga tidak boleh sama nama dengan kategori sistem berjenis sama (409).
7. Ubah `kind` kategori yang sudah dipakai transaksi: 409.
8. Ibu tidak boleh hapus dompet bersaldo: saat ini diperiksa dari `opening_balance` (dompet bertransaksi sudah ditolak 409).
9. `require_role` dari Chandra: setelah ada, ganti `services/akses.py`.
10. `Idempotency-Key`: belum ditangani; nama unik dompet sudah mencegah baris ganda (409).
11. `src/data/mockData.js` memakai "Makanan & Minuman"; frontend belum memakai endpoint ini (integrasi Minggu 4).
