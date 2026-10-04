-- ============================================================
-- Migrasi tabel categories (kategori sistem dan kategori rumah tangga)
-- Penulis: Gilang Nur Adha — potongan Dompet dan Kategori
-- Bergantung pada 0002_households.sql dan 0003_household_members.sql
-- Aman dijalankan berulang (create if not exists / drop policy if exists).
--
-- Keputusan yang dipakai di sini:
--   D3  TIDAK ada kolom deleted_at. Kategori diarsipkan lewat is_archived = true.
--   Seed delapan kategori sistem ada DI DALAM migrasi ini (bukan seed.sql),
--   karena dibutuhkan di produksi.
--   Jenis (kind) tiap kategori diambil dari cara mockData.js memakainya:
--   tujuh kategori dipakai baris pengeluaran, "Lainnya" dipakai baris
--   pemasukan (Gaji Januari pada mockData.js). Ini pertanyaan tim nomor 2,
--   konfirmasi ke tim frontend pada koordinasi Sabtu.
-- ============================================================

-- 1. Tipe jenis kategori -------------------------------------
do $$
begin
    create type public.category_kind as enum ('income', 'expense');
exception
    when duplicate_object then null;
end
$$;

-- 2. Tabel categories ----------------------------------------
-- household_id NULL berarti kategori sistem, dipakai semua rumah tangga.
create table if not exists public.categories (
    id            uuid primary key default gen_random_uuid(),
    household_id  uuid references public.households(id) on delete cascade,
    name          varchar(80) not null,
    kind          public.category_kind not null,
    icon          varchar(8),
    color         char(7) not null default '#94A3B8',
    is_system     boolean not null default false,
    is_archived   boolean not null default false,
    created_at    timestamptz not null default now(),
    updated_at    timestamptz not null default now(),
    constraint categories_nama_tidak_kosong check (length(btrim(name)) > 0),
    constraint categories_warna_heksadesimal check (color ~ '^#[0-9A-Fa-f]{6}$'),
    constraint categories_sistem_tanpa_rumah check ((household_id is null) = is_system)
);

-- Jebakan 1: indeks unik biasa pada (household_id, name) tidak mencegah nama
-- ganda di antara kategori sistem karena NULL dianggap berbeda di Postgres.
-- Karena itu dipakai dua indeks unik parsial.
-- nama unik di dalam satu rumah tangga
create unique index if not exists uq_categories_household_name
    on public.categories (household_id, name) where household_id is not null;
-- nama unik di antara kategori sistem
create unique index if not exists uq_categories_system_name
    on public.categories (name) where household_id is null;

create index if not exists idx_categories_household_kind
    on public.categories (household_id, kind);

-- 3. Pemicu updated_at ---------------------------------------
-- Fungsi public.set_updated_at() dibuat pada 0004_accounts.sql; diulang di sini
-- dengan isi yang sama supaya migrasi ini tetap aman bila dijalankan sendiri.
create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
    new.updated_at = now();
    return new;
end
$$;

drop trigger if exists trg_categories_updated_at on public.categories;
create trigger trg_categories_updated_at
    before update on public.categories
    for each row execute function public.set_updated_at();

-- 4. Kebijakan RLS -------------------------------------------
-- Semua anggota membaca kategori sistem dan kategori rumah tangganya.
-- Tambah, ubah, dan hapus hanya untuk ayah dan ibu (Bab 3.4), dan hanya untuk
-- kategori bukan sistem. Kategori sistem tidak bisa diubah siapa pun lewat API.
alter table public.categories enable row level security;

drop policy if exists kategori_baca_sistem_dan_rumah on public.categories;
create policy kategori_baca_sistem_dan_rumah on public.categories
    for select
    using (
        household_id is null
        or private.is_household_member(household_id)
    );

drop policy if exists kategori_tambah_ayah_ibu on public.categories;
create policy kategori_tambah_ayah_ibu on public.categories
    for insert
    with check (
        is_system = false
        and private.household_role(household_id) in ('ayah', 'ibu')
    );

drop policy if exists kategori_ubah_ayah_ibu on public.categories;
create policy kategori_ubah_ayah_ibu on public.categories
    for update
    using (
        is_system = false
        and private.household_role(household_id) in ('ayah', 'ibu')
    )
    with check (
        is_system = false
        and private.household_role(household_id) in ('ayah', 'ibu')
    );

drop policy if exists kategori_hapus_ayah_ibu on public.categories;
create policy kategori_hapus_ayah_ibu on public.categories
    for delete
    using (
        is_system = false
        and private.household_role(household_id) in ('ayah', 'ibu')
    );

-- 5. Seed delapan kategori sistem (aman diulang) -------------
-- Nama, ikon, dan warna diambil dari src/data/mockData.js supaya sama dengan
-- yang tampil di antarmuka. Indeks unik parsial uq_categories_system_name
-- menjaga agar menjalankan migrasi dua kali tidak menggandakan baris.
insert into public.categories (household_id, name, kind, icon, color, is_system) values
    (null, 'Makanan & Minuman', 'expense', '🍽️', '#F59E0B', true),
    (null, 'Transportasi',      'expense', '🚗', '#3B82F6', true),
    (null, 'Belanja',           'expense', '🛍️', '#EC4899', true),
    (null, 'Pendidikan',        'expense', '📚', '#8B5CF6', true),
    (null, 'Kesehatan',         'expense', '💊', '#10B981', true),
    (null, 'Tagihan & Utilitas','expense', '💡', '#F97316', true),
    (null, 'Hiburan',           'expense', '🎬', '#06B6D4', true),
    (null, 'Lainnya',           'income',  '📦', '#94A3B8', true)
on conflict (name) where household_id is null do nothing;
