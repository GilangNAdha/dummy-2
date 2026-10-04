# WAD_Kel11: KeluargaFin

Aplikasi web manajemen keuangan keluarga, proyek Kelompok 11 untuk mata kuliah **Web Application Development (WAD)**.

KeluargaFin membantu keluarga (Ayah, Ibu, Anak) mencatat pengeluaran bersama, memantau budget bulanan, dan memahami kondisi keuangan keluarga dari satu dashboard, **tanpa menghubungkan rekening bank dan tanpa kredensial bank**.

## Kelompok 11

- Nizar Hermawan
- Gilang Nur Adha
- Apri Kuncoro
- Chandra TW
- Arjuna Rangga Lengkey

## Teknologi

- React 19 + Vite
- Tailwind CSS 4
- React Router
- Backend: Python FastAPI dan Supabase
- localStorage: data demo tersimpan di browser
- Frontend hanya untuk rendering, tidak menghitung apa pun
- Seluruh aturan bisnis dan perhitungan ada di backend

## Menjalankan

Frontend:

```
npm install
npm run dev        # http://localhost:5173
```

Backend (rincian di `backend/README.md`):

```
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload   # dokumentasi di http://localhost:8000/docs
```

## Menghubungkan frontend ke backend

Dompet (`/accounts`) dan kategori (`/categories`) sudah tersambung ke endpoint
FastAPI lewat `src/API/apiClient.js`. Integrasi menyala bila tiga hal tersedia:

1. `VITE_API_URL` diisi (lihat `.env.example`), misalnya `http://localhost:8000/api/v1`
2. token sesi Supabase tersimpan di localStorage dengan kunci `kf_access_token`
3. id rumah tangga tersimpan dengan kunci `kf_household_id`

Selama ketiganya belum ada, aplikasi memakai mode lokal (localStorage) seperti
demo sekarang, sehingga demo tetap berjalan tanpa backend. Laporan lengkap
potongan dompet dan kategori ada di `docs/LAPORAN_DOMPET_DAN_KATEGORI.md`.

