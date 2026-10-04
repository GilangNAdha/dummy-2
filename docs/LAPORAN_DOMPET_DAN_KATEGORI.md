# Laporan kerja potongan Dompet dan Kategori

**Gilang Nur Adha — Kelompok 11, Web Application Development**
Sumber: `Panduan_Kerja_Gilang_Nur_Adha_KeluargaFin.pdf` (4 Oktober 2026).
Berkas kode: migrasi `0004`/`0005`, `seed.sql`, router `accounts.py`/`categories.py`, uji `test_dompet.py`/`test_kategori.py`, koleksi `tests/koleksi/`.

---

## 1. Ringkasan pekerjaan

| No | Pekerjaan | Keluaran | Status |
| --- | --- | --- | --- |
| K1 | Migrasi tabel accounts | `backend/supabase/migrations/0004_accounts.sql` | selesai, terverifikasi |
| K2 | Migrasi categories + seed 8 kategori sistem | `backend/supabase/migrations/0005_categories.sql` | selesai, terverifikasi |
| K3 | Data contoh dompet | `backend/supabase/seed.sql` | selesai |
| K4 | Router CRUD /accounts (5 endpoint) | `backend/app/api/v1/accounts.py` | selesai, 100% cakupan uji |
| K5 | Koleksi permintaan uji + uji lintas rumah tangga | `backend/tests/koleksi/` | selesai |
| K6 | Router CRUD /categories (5 endpoint) | `backend/app/api/v1/categories.py` | selesai, 99% cakupan uji |
| K7 | Pemeriksaan peran dua lapis | `backend/app/core/peran.py` + RLS | selesai |
| K8 | Pengujian otomatis pytest | `backend/tests/test_dompet.py`, `test_kategori.py` | 95 uji lulus, cakupan 91% |
| K9 | Integrasi frontend dompet dan kategori | `src/API/apiClient.js`, `src/API/getData.js`, `src/pages/Settings.jsx` | selesai (mode API + mode lokal) |
| K10 | Temuan uji kontrak | bagian 5 laporan ini | 6 temuan ditutup, 5 dicatat |

Sepuluh endpoint sudah terdaftar dan tampil di `/docs`:

| Endpoint | Sukses | Penolakan |
| --- | --- | --- |
| `GET /api/v1/accounts` | 200 | 400 tanpa `household_id`, 401 tanpa token |
| `GET /api/v1/accounts/{id}` | 200 | 401, 404 |
| `POST /api/v1/accounts` | 201 | 400, 401, 403 peran anak, 409 nama ganda |
| `PATCH /api/v1/accounts/{id}` | 200 | 400 badan kosong, 403, 404, 409 |
| `DELETE /api/v1/accounts/{id}` | 200 | 403, 404, 409 masih dipakai transaksi |
| `GET /api/v1/categories` | 200 | 400, 401 |
| `GET /api/v1/categories/{id}` | 200 | 401, 404 |
| `POST /api/v1/categories` | 201 | 400, 403, 409 |
| `PATCH /api/v1/categories/{id}` | 200 | 400, 403 kategori sistem, 404, 409 |
| `DELETE /api/v1/categories/{id}` | 200 | 403 kategori sistem, 404 |

## 2. Berkas yang ditambah dan diubah

Ditambah:

```
backend/supabase/migrations/0004_accounts.sql
backend/supabase/migrations/0005_categories.sql
backend/supabase/seed.sql
backend/app/api/v1/accounts.py
backend/app/api/v1/categories.py
backend/app/core/peran.py
backend/tests/test_dompet.py
backend/tests/test_kategori.py
backend/tests/koleksi/dompet_kategori.http
backend/tests/koleksi/uji_rls_lintas_rumah_tangga.http
backend/tests/koleksi/README.md
backend/.env.example
.env.example
.gitignore
src/API/apiClient.js
docs/LAPORAN_DOMPET_DAN_KATEGORI.md
```

Diubah (seminimal mungkin):

```
backend/app/main.py                    dua baris pemasangan router
backend/app/core/supabase_client.py    pemetaan galat 409 dan 403 (temuan T2)
backend/tests/test_klien.py            empat uji untuk pemetaan galat
src/API/getData.js                     tujuh fungsi potongan ini memakai endpoint
src/API/adapters.js                    ikon dompet diturunkan dari jenis (tabel tanpa kolom icon)
src/pages/Settings.jsx                 galat backend ditampilkan lewat useToast
vite.config.js                         host dan allowedHosts untuk pratinjau pengembangan
```

## 3. Keputusan yang diambil

| Sumber | Keputusan | Alasan |
| --- | --- | --- |
| D1 | `accounts` tanpa `current_balance` | Ikut dokumen v3.0. Saldo awal disimpan, saldo berjalan tidak disimpan supaya tidak bisa basi. |
| D3 | Tidak ada `deleted_at` di kedua tabel | Pengarsipan memakai `is_active` (dompet) dan `is_archived` (kategori). |
| Pertanyaan 3 | `CHECK (opening_balance >= 0)` | Kosisten dengan aturan uang bilangan bulat. Hapus constraint bila tim ingin mengizinkan saldo awal negatif. |
| Pertanyaan 4 | Kategori sistem ditolak `403 FORBIDDEN` | Aturan tentang jenis baris, bukan bentrok data. |
| Pertanyaan 5 | `supabase_client` meneruskan 409 dan 403 | Diperbaiki di klien (`KonflikData`), lihat temuan T2. |
| Pertanyaan 6 | Memakai fungsi bantu milik 0003 | `private.is_household_member()` dan `private.household_role()` dipakai ulang, tidak membuat duplikat. |
| Pertanyaan 9 | Skema Pydantic di berkas router | Mengikuti pola `ProfilUbah` pada `profiles.py`, tanpa folder `app/schemas`. |
| Pertanyaan 10 | Koleksi di `backend/tests/koleksi/` | Sesuai saran awal panduan. |
| Pertanyaan 2 | Delapan kategori sistem dari `mockData.js` | Jenis ditentukan dari pemakaian pada mock: tujuh kategori dipakai baris pengeluaran, "Lainnya" dipakai baris pemasukan. **Perlu konfirmasi tim frontend.** |
| Pertanyaan 7 | Seed menargetkan rumah tangga `Keluarga Santoso` | Bila nama rumah tangga contoh berbeda, ganti klausa `where` pada `seed.sql`. |

## 4. Bukti pengujian

### 4.1 Verifikasi migrasi pada basis data kosong

Karena Supabase CLI tidak tersedia di lingkungan ini, migrasi diverifikasi pada
PostgreSQL 16 lokal dengan tiruan skema `auth` Supabase (tabel `auth.users` dan
fungsi `auth.uid()`). Cara mengulang:

```bash
# 1. siapkan tiruan Supabase: peran anon/authenticated, skema auth, auth.uid()
# 2. jalankan migrasi berurutan: 0001, 0002, 0003, 0004, 0005
# 3. jalankan ulang seluruh migrasi untuk membuktikan idempotensi
# 4. jalankan pemeriksaan checklist langkah 1.4, 2.7, dan uji RLS 7.2
```

Hasil: **35 pemeriksaan lulus, 0 gagal.** Ringkasannya:

- `accounts` punya 9 kolom, tanpa `current_balance` (D1) dan tanpa `deleted_at` (D3), RLS aktif, 4 kebijakan RLS.
- Menjalankan seluruh migrasi dua kali tidak menimbulkan galat.
- Nama dompet ganda ditolak 23505; `opening_balance` negatif, nama kosong, dan jenis di luar enum ditolak.
- `categories` berisi tepat 8 kategori sistem, semuanya `household_id is null`; 4 kebijakan RLS.
- Warna bukan heksadesimal ditolak; `household_id` kosong dengan `is_system=false` ditolak; kategori rumah tangga bertanda sistem ditolak; nama kategori sistem ganda ditolak.
- Kategori rumah tangga boleh bernama sama dengan kategori sistem (dua indeks unik parsial bekerja).
- RLS: peran anak ditolak saat menambah dompet dan kategori (galat 42501); ibu boleh menambah dompet; pengguna rumah tangga B melihat 0 dompet rumah tangga A; kategori sistem terbaca semua rumah tangga tetapi tidak ada baris kategori sistem yang berubah walau di-PATCH.
- `seed.sql` mengisi tiga dompet contoh untuk rumah tangga contoh dan aman dijalankan dua kali.

### 4.2 Pengujian otomatis

```bash
cd backend
pytest -q                                     # 95 passed
pytest -q --cov=app --cov-report=term-missing # cakupan 91%
```

| Modul | Cakupan |
| --- | --- |
| `app/api/v1/accounts.py` | 100% |
| `app/api/v1/categories.py` | 99% |
| `app/core/peran.py` | 100% |
| seluruh `app/` | 91% |

Kasus yang diuji sesuai tabel panduan 7.1: tanpa token (401), tanpa `household_id` (400),
daftar dengan meta dan links, penyaring terbawa ke links, `per_page` 500 dibatasi 100,
sort tak dikenal (400), detail ada/tidak ada (200/404), tambah sah (201), nama kosong,
jenis tak dikenal, saldo negatif, saldo desimal (400), nama ganda (409), PATCH sebagian
(200), badan kosong (400), `household_id` dikirim saat PATCH (400), PATCH tidak ada (404),
DELETE sah (200), DELETE dipakai transaksi (409), peran anak pada POST/PATCH/DELETE (403),
daftar kategori memuat kategori sistem, warna "merah" (400), `is_system` dari klien (400),
ubah dan hapus kategori sistem (403), dan nama sama dengan kategori sistem (409).
Header `X-Request-Id` diperiksa pada respons pertama uji daftar.

### 4.3 Uji lintas rumah tangga (langkah 7.2)

Perintah curl tersimpan di `backend/tests/koleksi/uji_rls_lintas_rumah_tangga.http`.
Pada harness PostgreSQL lokal, hasilnya: token rumah tangga B membaca dompet rumah
tangga A = 0 baris, kunci anon tanpa token = 0 baris, token anak menambah dompet =
galat RLS (42501), PATCH kategori sistem oleh ayah rumah tangga B = 0 baris berubah.
Uji ini harus diulang pada Supabase nyata sebelum presentasi dan tangkapan layarnya
disimpan sebagai bukti butir 2 dan 9 Lampiran B.

### 4.4 Frontend

```bash
npm run build     # berhasil, 44 modul
```

## 5. Temuan uji kontrak (K10)

| No | Temuan | Tindakan |
| --- | --- | --- |
| T1 | `supabase db reset` belum bisa jalan dari basis data kosong: migrasi `0009_goal_contributions.sql` mengacu ke `public.transactions`, sedangkan migrasi `0006` (transactions) dan `0007` (budgets) milik Apri belum ada. | **Dibuka, blokir untuk Apri.** Beri tahu Apri dan Chandra. Setelah 0006 dan 0007 masuk, seluruh rantai migrasi dapat dijalankan dari kosong. |
| T2 | `supabase_client._cek` mengubah semua galat 4xx PostgREST menjadi 502, sehingga 409 nama ganda dan 403 RLS tidak pernah sampai ke klien. | **Ditutup.** Kode 23505/23503 menjadi 409 `CONFLICT` (kelas `KonflikData`), kode 42501 dan status 401/403 menjadi 403 `FORBIDDEN`. Empat uji baru di `tests/test_klien.py`. Jawaban pertanyaan tim nomor 5. |
| T3 | Kolom `bigint` membulatkan nilai desimal: memasukkan `1000.5` tersimpan sebagai `1001`, jadi basis data tidak menolak desimal. | **Ditutup.** Aturan uang bilangan bulat ditegakkan di API lewat `StrictInt` (400), bukan lewat CHECK. Diuji pada `test_dompet.py`. |
| T4 | Panduan menyebut garis dasar `pytest -q` = 17 lulus; keadaan repositori sudah 30 lulus, dan setelah pekerjaan ini 95 lulus. | **Ditutup.** Garis dasar baru dicatat di laporan ini. |
| T5 | Berkas `docs/RENCANA_INTEGRASI_FRONTEND.md` yang wajib dibaca pada langkah 0.4 tidak ada di repositori. | **Dibuka.** Minta berkas itu ke tim frontend; materi kuliah yang harus tetap tampak sudah dipertahankan pada `getData.js` (alur data, `map`, `console.log`, `useFetch`, localStorage). |
| T6 | `backend/README.md` menyuruh menyalin `.env.example`, tetapi berkas itu tidak ada. | **Ditutup.** Dibuat `backend/.env.example` dan `.env.example` frontend. |
| T7 | Penolong `list_response` meneruskan `extra` apa adanya; router sempat mengirim penyaring bergaya PostgREST (`household_id=eq...`) sehingga `links` tidak bisa diikuti klien. | **Ditutup.** Router mengirim parameter API biasa; ditemukan oleh uji `test_penyaring_terbawa_ke_tautan`. |
| T8 | `require_role` milik Chandra (deps.py) belum ada, sedangkan langkah 6 memakainya di Minggu 3. | **Ditutup sementara.** Dibuat `app/core/peran.py` (`wajib_penulis`) sebagai pengganti; isinya bisa dipindah ke `deps.py` tanpa mengubah pemeriksaan. |
| T9 | `adapters.js` menyebut `current_balance` dan `saved_amount` sebagai kolom turunan backend, sedangkan router yang ada belum menghitungnya. | **Dibuka.** `accountFromApi` sudah jatuh ke `opening_balance`. Penghitungan saldo berjalan perlu keputusan tim (D1) sebelum diandalkan. |
| T10 | Integrasi frontend baru bisa dinyalakan setelah Supabase Auth di frontend selesai (token dan id rumah tangga disimpan di localStorage). | **Dibuka.** `apiClient.js` membaca `kf_access_token` dan `kf_household_id`; sampai halaman masuk mengisinya, aplikasi tetap memakai mode lokal. |
| T11 | Jawaban 409 "Dompet masih dipakai transaksi." belum bisa diuji dari basis data nyata sebelum migrasi 0006 masuk. | **Dibuka, menunggu Apri.** Sudah diuji dengan fungsi palsu (unit test). |

## 6. Bahan presentasi (K11)

### 6.1 Naskah 3 menit: alur autentikasi Supabase dan aturan peran

| Waktu | Ucapan |
| --- | --- |
| 0:00-0:30 | "Backend kami tidak menyimpan kata sandi dan tidak menerbitkan token. Pendaftaran, masuk, penyegaran token, dan pemulihan kata sandi diserahkan ke Supabase Auth." |
| 0:30-1:20 | "Klien masuk lewat supabase-js, menerima access token berumur pendek dan refresh token. Setiap permintaan ke FastAPI membawa `Authorization: Bearer <token>`. Di basis data, sebuah pemicu membuat baris `profiles` otomatis tepat setelah pendaftaran." |
| 1:20-2:00 | "FastAPI memeriksa tanda tangan token lewat kunci publik JWKS dengan algoritme ES256 atau RS256, memeriksa masa berlaku, dan memastikan audience `authenticated`. Bila gagal, jawabannya 401 UNAUTHENTICATED. Untuk pengembangan lokal dipakai HS256 dengan rahasia bersama." |
| 2:00-2:40 | "Peran ayah, ibu, dan anak disimpan di tabel `household_members`, bukan di dalam token, sehingga perubahan peran langsung berlaku. Pemeriksaan peran ada di dua lapis: `wajib_penulis` di FastAPI memberi pesan yang jelas, dan RLS di basis data menjadi pengaman terakhir." |
| 2:40-3:00 | "Kunci anon aman dipakai di klien karena dibatasi RLS, sedangkan service_role hanya untuk server dan migrasi. Token asli pengguna diteruskan ke PostgREST supaya RLS berlaku sebagai pengguna itu." |

### 6.2 Naskah 4 menit: demo dompet dan kategori

| Waktu | Aksi | Penjelasan |
| --- | --- | --- |
| 0:00-0:30 | Tunjukkan ERD `accounts` dan `categories` | `household_id` sebagai batas data, uang BIGINT, kategori sistem ber-`household_id` kosong |
| 0:30-1:30 | `GET /accounts`, `POST` dompet DANA, `PATCH` ganti nama | Paginasi `{data, meta, links}`, jawaban 201, PATCH sebagian |
| 1:30-2:15 | `POST` nama ganda (409), `DELETE` dompet yang punya transaksi (409), `DELETE` dompet baru (200) | Kunci asing RESTRICT, pengarsipan lewat `is_active` |
| 2:15-3:15 | `GET /categories` memuat 8 kategori sistem, `POST` kategori baru, nama ganda 409, `DELETE` kategori sistem ditolak | Seed sistem, dua indeks unik parsial, `is_system` |
| 3:15-4:00 | Token anak `POST /accounts` (403), token rumah tangga lain `GET` dompet A (kosong) | RLS dan peran dua lapis |

### 6.3 Slide bagian ini

1. Potongan dan peran: dompet dan kategori, 10 endpoint dari total 42 endpoint.
2. ERD `accounts` dan `categories` beserta aturan hapus (RESTRICT, SET NULL, CASCADE).
3. Aturan integritas dan RLS: dua indeks unik parsial, tiga CHECK, kebijakan per peran.
4. Kontrak endpoint dengan satu contoh permintaan dan respons.
5. Hasil uji: 95 uji lulus, cakupan 91%, uji lintas rumah tangga, tautan PR.
6. Satu slide alur autentikasi dan peran untuk bagian 3 menit.

## 7. Daftar periksa akhir (bagian 15 panduan)

**Basis data**

- [x] Migrasi 0004 dan 0005 aman dijalankan berulang; 35 pemeriksaan lulus pada PostgreSQL lokal.
- [ ] `supabase db reset` dari kosong — **tertahan** sampai migrasi 0006 dan 0007 (Apri) masuk (temuan T1).
- [x] `accounts`: 4 kebijakan, indeks unik `(household_id, name)`, CHECK nama dan saldo.
- [x] `categories`: 4 kebijakan, dua indeks unik parsial, tiga CHECK, 8 kategori sistem tanpa ganda.
- [x] Tidak ada `current_balance` dan tidak ada `deleted_at` pada kedua tabel.
- [x] Data contoh hanya di `seed.sql`, tidak di migrasi.

**API**

- [x] Sepuluh endpoint tampil di `/docs`.
- [x] Bentuk balasan seragam: `data`, `meta`, `links`; galat `error`.
- [x] Kode 200, 201, 400, 401, 403, 404, 409 diuji di tempat yang tepat.
- [x] `household_id` disaring pada setiap query; tidak ada agregat dan tidak ada service_role.
- [x] Header `X-Request-Id` ada di setiap respons.

**Pengujian dan bukti**

- [x] Seluruh suite hijau (95 uji), cakupan 91% untuk kode `app/`.
- [x] Perintah uji lintas rumah tangga tersimpan di `backend/tests/koleksi/`.
- [ ] Tangkapan layar 403 peran anak dan hasil uji lintas rumah tangga pada Supabase nyata (dijalankan sebelum 18 Oktober).
- [x] Koleksi permintaan uji untuk 10 endpoint ada di repositori.

**Kontribusi dan presentasi**

- [x] Riwayat commit berbahasa Indonesia, tanpa emoticon, menyebut tabel atau endpoint.
- [ ] Tinjauan PR anggota lain (K13, dikerjakan tiap minggu).
- [ ] Slide dan naskah difinalkan 25 Oktober, gladi bersih 27 Oktober, presentasi 28 Oktober.

## 8. Jawaban untuk daftar pertanyaan tim (bagian 16)

| No | Pertanyaan | Pegangan yang dipakai sekarang |
| --- | --- | --- |
| 1 | Saldo berjalan dihitung frontend atau backend? | Ikut v3.0: tanpa `current_balance`. Perlu dipastikan karena `adapters.js` menyebut kolom turunan. |
| 2 | Delapan kategori sistem apa saja? | Diambil dari `mockData.js`; jenis ditentukan dari pemakaian mock. Perlu konfirmasi tim frontend. |
| 3 | `opening_balance` boleh negatif? | Tidak, ada CHECK `>= 0`. |
| 4 | Kode untuk kategori sistem? | 403 FORBIDDEN. |
| 5 | Apakah klien meneruskan 409 dan 403? | Ya, sudah diperbaiki dan diuji (T2). |
| 6 | Nama enum peran dan fungsi bantu keanggotaan? | `member_role` dengan nilai `ayah`, `ibu`, `anak`; fungsi `private.is_household_member()` dan `private.household_role()`. |
| 7 | Nama rumah tangga contoh dan akun peran? | Seed memakai `Keluarga Santoso`; ganti bila berbeda. |
| 8 | Header `Idempotency-Key`? | Belum ditangani; milik Chandra. Tidak dipakai pada potongan ini. |
| 9 | Folder `schemas` dan `repositories`? | Tidak dibuat; skema ditaruh di berkas router mengikuti `profiles.py`. |
| 10 | Lokasi koleksi permintaan uji? | `backend/tests/koleksi/`. |

## 9. Cara menjalankan ulang pemeriksaan

```bash
# backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt pytest-cov
pytest -q                                      # 95 passed
pytest -q --cov=app --cov-report=term-missing  # cakupan 91%

# frontend
cd ..
npm install
npm run build                                  # berhasil
```

Dengan Supabase lokal (setelah migrasi 0006 dan 0007 tersedia):

```bash
cd backend
supabase start
supabase db reset        # menjalankan 0001-0009 lalu seed.sql
uvicorn app.main:app --reload
# buka http://localhost:8000/docs
```
