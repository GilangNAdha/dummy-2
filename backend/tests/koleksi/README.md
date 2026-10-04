# Koleksi permintaan uji — dompet dan kategori

Bukti butir 4 Lampiran B: koleksi berisi 10 endpoint potongan dompet dan kategori,
masing-masing dengan contoh sukses dan contoh gagal.

| Berkas | Isi |
| --- | --- |
| `dompet_kategori.http` | 20 permintaan ke FastAPI: 10 endpoint ditambah 10 kasus gagal (400, 401, 403, 409) |
| `uji_rls_lintas_rumah_tangga.http` | Lima permintaan langsung ke PostgREST dengan kunci anon, di luar FastAPI, untuk membuktikan RLS menolak |

## Cara menjalankan

1. Jalankan basis data dan layanan:

   ```bash
   cd backend
   supabase start
   supabase db reset          # menjalankan migrasi 0001 sampai 0005 lalu seed.sql
   uvicorn app.main:app --reload
   ```

2. Ambil token pengguna uji dari Supabase Auth (satu ayah, satu ibu, satu anak,
   ditambah satu pengguna rumah tangga lain):

   ```bash
   curl -s -X POST "$SUPABASE_URL/auth/v1/token?grant_type=password" \
     -H "apikey: $SUPABASE_ANON_KEY" -H "Content-Type: application/json" \
     -d '{"email":"ayah@contoh.id","password":"..."}'
   ```

3. Buka berkas `.http` dengan ekstensi REST Client (VS Code) atau tukar ke Postman,
   lalu isi variabel di bagian atas berkas.

4. Jalankan berurutan. Nomor 3 (POST dompet) dijalankan dua kali untuk melihat
   jawaban 409 nama ganda.

## Hasil yang diharapkan

| Permintaan | Jawaban |
| --- | --- |
| 1 GET daftar dompet | 200, `{data, meta, links}`, `links.next` memuat penyaring |
| 2 GET tanpa household_id | 400 VALIDATION_ERROR, `details[0].field = household_id` |
| 3 POST dompet | 201 pertama, 409 kedua |
| 4 PATCH dompet | 200; 409 bila nama diubah menjadi nama yang sudah dipakai |
| 5 DELETE dompet | 200 `{"data": null, "message": "baris dihapus"}`; 409 bila masih dipakai transaksi |
| 6 GET kategori | 200, delapan kategori sistem ikut terbaca |
| 7 POST kategori | 201; warna `merah` ditolak 400 |
| 8 GET detail kategori | 200 untuk kategori rumah tangga dan kategori sistem |
| 9 PATCH kategori | 200; kategori sistem ditolak 403 |
| 10 DELETE kategori | 200; kategori sistem ditolak 403 |
| 11 tanpa token | 401 UNAUTHENTICATED, ada header `X-Request-Id` |
| 12 sampai 14 token anak | 403 FORBIDDEN |
| 15 token rumah tangga lain | 200 dengan `data: []` |
| 16 saldo desimal | 400, `StrictInt` menolak 1000.5 |
| 17 badan kosong | 400 "Tidak ada kolom yang diubah." |
| 18 memindahkan rumah tangga | 400, `extra="forbid"` |
| 19 is_system dari klien | 400 |
| 20 sort tak dikenal | 400 |

Untuk `uji_rls_lintas_rumah_tangga.http`: permintaan 1, 2, dan 4 harus tidak
mengembalikan baris apa pun, permintaan 3 harus gagal dengan kode Postgres 42501,
dan permintaan 5 boleh mengembalikan baris. Simpan tangkapan layarnya — itu bukti
butir 2 dan 9 Lampiran B.

## Catatan

- Uji lintas rumah tangga memerlukan basis data nyata. Pada repositori ini berkas
  uji otomatis (`tests/test_dompet.py`, `tests/test_kategori.py`) mengganti akses
  basis data dengan fungsi palsu, jadi uji itu membuktikan perilaku router, bukan RLS.
- Sebelum migrasi 0006 (transactions) milik Apri masuk, jawaban 409 "Dompet masih
  dipakai transaksi." belum bisa diuji dari basis data nyata karena tabel
  rujukannya belum ada.
