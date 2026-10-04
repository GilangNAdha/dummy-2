-- ============================================================
-- Migrasi tabel accounts (dompet, rekening, dompet digital)
-- Penulis: Gilang Nur Adha — potongan Dompet dan Kategori
-- Bergantung pada 0002_households.sql dan 0003_household_members.sql
-- Aman dijalankan berulang (create if not exists / drop policy if exists).
--
-- Keputusan yang dipakai di sini (lihat juga bagian 3.2 panduan kerja):
--   D1  Tabel hanya menyimpan fakta mentah. TIDAK ada kolom current_balance;
--       saldo berjalan tidak disimpan supaya tidak bisa basi.
--   D3  TIDAK ada kolom deleted_at. Dompet diarsipkan lewat is_active = false.
--   Pertanyaan tim nomor 3: CHECK opening_balance >= 0 dipakai agar konsisten
--       dengan aturan uang bilangan bulat. Bila tim ingin mengizinkan saldo
--       awal negatif (kartu kredit), hapus constraint accounts_saldo_awal_tidak_negatif.
-- ============================================================

-- 1. Tipe jenis dompet ---------------------------------------
do $$
begin
    create type public.account_type as enum ('bank', 'cash', 'ewallet');
exception
    when duplicate_object then null;
end
$$;

-- 2. Tabel accounts ------------------------------------------
create table if not exists public.accounts (
    id               uuid primary key default gen_random_uuid(),
    household_id     uuid not null references public.households(id) on delete restrict,
    name             varchar(80) not null,
    type             public.account_type not null,
    provider         varchar(60),
    opening_balance  bigint not null default 0,
    is_active        boolean not null default true,
    created_at       timestamptz not null default now(),
    updated_at       timestamptz not null default now(),
    constraint accounts_nama_tidak_kosong check (length(btrim(name)) > 0),
    constraint accounts_saldo_awal_tidak_negatif check (opening_balance >= 0)
);

-- satu rumah tangga tidak boleh punya dua dompet bernama sama
create unique index if not exists uq_accounts_household_name
    on public.accounts (household_id, name);

-- daftar dompet per rumah tangga, urut terbaru
create index if not exists idx_accounts_household_created
    on public.accounts (household_id, created_at desc);

-- 3. Pemicu updated_at ---------------------------------------
-- Dipakai bersama oleh tabel lain (fungsi yang sama, aman dijalankan berulang).
create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
    new.updated_at = now();
    return new;
end
$$;

drop trigger if exists trg_accounts_updated_at on public.accounts;
create trigger trg_accounts_updated_at
    before update on public.accounts
    for each row execute function public.set_updated_at();

-- 4. Kebijakan RLS -------------------------------------------
-- Aturan Bab 3.4: semua anggota rumah tangga boleh membaca;
-- hanya ayah dan ibu yang boleh menambah, mengubah, dan menghapus.
-- Identitas diambil dari auth.uid() (token Supabase), bukan dari data kiriman.
-- Fungsi pembantu keanggotaan dipakai ulang dari 0003 agar tidak ada duplikat.
alter table public.accounts enable row level security;

drop policy if exists dompet_baca_anggota_rumah on public.accounts;
create policy dompet_baca_anggota_rumah on public.accounts
    for select
    using (
        private.is_household_member(household_id)
    );

drop policy if exists dompet_tambah_ayah_ibu on public.accounts;
create policy dompet_tambah_ayah_ibu on public.accounts
    for insert
    with check (
        private.household_role(household_id) in ('ayah', 'ibu')
    );

drop policy if exists dompet_ubah_ayah_ibu on public.accounts;
create policy dompet_ubah_ayah_ibu on public.accounts
    for update
    using (
        private.household_role(household_id) in ('ayah', 'ibu')
    )
    with check (
        private.household_role(household_id) in ('ayah', 'ibu')
    );

drop policy if exists dompet_hapus_ayah_ibu on public.accounts;
create policy dompet_hapus_ayah_ibu on public.accounts
    for delete
    using (
        private.household_role(household_id) in ('ayah', 'ibu')
    );
