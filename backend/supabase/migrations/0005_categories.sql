-- ============================================================
-- Migrasi tabel categories (kategori pemasukan dan pengeluaran)
-- Penulis: Gilang Nur Adha
-- Kategori sistem : household_id NULL, is_system TRUE, terlihat semua rumah tangga.
-- Kategori keluarga: household_id terisi, is_system FALSE.
-- ============================================================

-- 1. Enum jenis kategori
do $$ begin
    create type category_kind as enum ('income', 'expense');
exception
    when duplicate_object then null;
end $$;

-- 2. Tabel categories
-- households -> categories CASCADE hanya berlaku pada kategori buatan keluarga;
-- kategori sistem (household_id NULL) tidak terikat rumah tangga mana pun.
create table if not exists public.categories (
    id           uuid primary key default gen_random_uuid(),
    household_id uuid references public.households(id) on delete cascade,
    name         varchar(80) not null,
    kind         category_kind not null,
    icon         varchar(8),
    color        char(7) not null default '#94A3B8',
    is_system    boolean not null default false,
    is_archived  boolean not null default false,
    created_at   timestamptz not null default now(),
    updated_at   timestamptz not null default now(),
    constraint ck_categories_warna  check (color ~ '^#[0-9A-Fa-f]{6}$'),
    constraint ck_categories_sistem check (is_system = (household_id is null))
);

-- unik per rumah tangga
create unique index if not exists uq_categories_household_name
    on public.categories (household_id, name);

-- NULL dianggap berbeda pada indeks unik, jadi nama kategori sistem dijaga indeks parsial
create unique index if not exists uq_categories_sistem_name
    on public.categories (name)
    where household_id is null;

create index if not exists idx_categories_household
    on public.categories (household_id);

drop trigger if exists trg_categories_updated_at on public.categories;
create trigger trg_categories_updated_at
    before update on public.categories
    for each row execute function public.set_updated_at();

-- 3. RLS
alter table public.categories enable row level security;

-- baca: kategori sistem ATAU kategori rumah tangga sendiri
drop policy if exists kategori_baca_anggota on public.categories;
create policy kategori_baca_anggota on public.categories
    for select
    using (
        household_id is null
        or household_id in (
            select household_id from public.household_members
            where user_id = auth.uid()
        )
    );

-- tulis: hanya kategori keluarga (bukan sistem), oleh ayah atau ibu
drop policy if exists kategori_tulis_ayah_ibu on public.categories;
create policy kategori_tulis_ayah_ibu on public.categories
    for all
    using (
        is_system = false
        and household_id in (
            select household_id from public.household_members
            where user_id = auth.uid() and role in ('ayah', 'ibu')
        )
    )
    with check (
        is_system = false
        and household_id in (
            select household_id from public.household_members
            where user_id = auth.uid() and role in ('ayah', 'ibu')
        )
    );

-- 4. Seed delapan kategori sistem (ada di migrasi agar ikut terpasang di produksi)
-- [PERLU DISEPAKATI] daftar nama final, lihat docs/DOMPET_DAN_KATEGORI.md
insert into public.categories (household_id, name, kind, icon, color, is_system) values
    (null, 'Makanan dan Minuman',  'expense', '🍽️', '#F59E0B', true),
    (null, 'Transportasi',         'expense', '🚗', '#3B82F6', true),
    (null, 'Belanja',              'expense', '🛍️', '#EC4899', true),
    (null, 'Pendidikan',           'expense', '📚', '#8B5CF6', true),
    (null, 'Kesehatan',            'expense', '💊', '#10B981', true),
    (null, 'Tagihan dan Utilitas', 'expense', '💡', '#F97316', true),
    (null, 'Hiburan',              'expense', '🎬', '#06B6D4', true),
    (null, 'Gaji',                 'income',  '💼', '#22C55E', true)
on conflict do nothing;
