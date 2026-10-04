-- ============================================================
-- seed.sql — data contoh untuk pengembangan dan pengujian lokal
-- Dijalankan otomatis oleh `supabase db reset` SETELAH semua migrasi.
-- Data contoh TIDAK boleh dipakai di produksi.
--
-- Berkas ini dipakai bersama oleh seluruh anggota tim. Tambahkan bagian
-- Anda di bawah komentar pembatas agar tidak bentrok saat digabungkan.
-- ============================================================

-- ===== seed: dompet contoh (Gilang), hanya pengembangan dan pengujian =====
-- SESUAIKAN: 'Keluarga Santoso' adalah rumah tangga contoh milik Nizar/Chandra
-- (lihat Lampiran A langkah 59). Bila nama rumah tangga contoh berbeda, ganti
-- nilai pada klausa where di bawah. Bila rumah tangganya belum ada, bagian ini
-- tidak menghasilkan baris (aman, tidak menimbulkan galat).
insert into public.accounts (household_id, name, type, provider, opening_balance)
select h.id, v.name, v.type::public.account_type, v.provider, v.opening_balance
from public.households h
cross join (values
    ('BCA Utama', 'bank',    'BCA',   5000000),
    ('Tunai',     'cash',    null,     500000),
    ('GoPay',     'ewallet', 'GoPay',  250000)
) as v(name, type, provider, opening_balance)
where h.name = 'Keluarga Santoso'
  and h.deleted_at is null
on conflict (household_id, name) do nothing;

-- Periksa hasilnya (dari basis data kosong, tiga baris):
--   select name, type, opening_balance from public.accounts order by name;
-- ===== akhir bagian Gilang =====
