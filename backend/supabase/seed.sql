-- ============================================================
-- Data contoh untuk pengembangan lokal (dijalankan oleh `supabase db reset`, BUKAN db push)
-- Bagian dompet contoh, penulis: Gilang Nur Adha
-- Membutuhkan rumah tangga contoh "Keluarga Santoso" (data contoh Nizar/Chandra).
-- Bila rumah tangga itu belum ada, tidak ada baris yang ditambahkan.
-- ============================================================

insert into public.accounts (household_id, name, type, provider, opening_balance)
select h.id, d.name, d.type::account_type, d.provider, d.opening_balance
from public.households h
cross join (values
    ('BCA Utama', 'bank',    'BCA',    8500000),
    ('Tunai',     'cash',    null,      750000),
    ('GoPay',     'ewallet', 'GoPay',   320000)
) as d(name, type, provider, opening_balance)
where h.name = 'Keluarga Santoso'
on conflict (household_id, name) do nothing;
