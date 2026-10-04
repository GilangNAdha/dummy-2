-- ============================================================
-- Migrasi tabel categories (kategori pemasukan dan pengeluaran)
-- Penulis: Gilang Nur Adha
-- Kategori sistem: household_id NULL, is_system TRUE, dipakai semua keluarga, tidak bisa diubah.
-- Kategori keluarga: household_id terisi, is_system FALSE.
-- ============================================================

-- 1. Enum jenis kategori
do $$ begin
    create type category_kind as enum ('income', 'expense');
exception
    when duplicate_object then null;
end $$;

-- 2. Tabel categories
create table if not exists public.categories (
    id           uuid primary key default gen_random_uuid(),
    household_id uuid references public.households(id) on delete cascade,
    name         varchar(60) not null,
    kind         category_kind not null default 'expense',
    icon         varchar(8),
    color        char(7) not null default '#94A3B8',
    parent_id    uuid references public.categories(id) on delete set null,
    is_system    boolean not null default false,
    is_archived  boolean not null default false,
    created_at   timestamptz not null default now(),
    updated_at   timestamptz not null default now(),
    constraint ck_categories_sistem check (is_system = (household_id is null)),
    constraint ck_categories_warna  check (color ~ '^#[0-9A-Fa-f]{6}$'),
    constraint ck_categories_induk  check (parent_id is null or parent_id <> id)
);

-- nama unik: global untuk kategori sistem, per rumah tangga untuk kategori keluarga
create unique index if not exists uq_categories_sistem_name
    on public.categories (name)
    where household_id is null;

create unique index if not exists uq_categories_household_name
    on public.categories (household_id, name)
    where household_id is not null;

drop trigger if exists trg_categories_updated_at on public.categories;
create trigger trg_categories_updated_at
    before update on public.categories
    for each row execute function public.set_updated_at();

-- 3. RLS
alter table public.categories enable row level security;

drop policy if exists kategori_baca on public.categories;
create policy kategori_baca on public.categories
    for select
    using (household_id is null or private.is_household_member(household_id));

drop policy if exists kategori_tambah on public.categories;
create policy kategori_tambah on public.categories
    for insert
    with check (
        household_id is not null
        and is_system = false
        and private.household_role(household_id) in ('ayah', 'ibu')
    );

drop policy if exists kategori_ubah on public.categories;
create policy kategori_ubah on public.categories
    for update
    using (household_id is not null and private.household_role(household_id) in ('ayah', 'ibu'))
    with check (household_id is not null and is_system = false
                and private.household_role(household_id) in ('ayah', 'ibu'));

drop policy if exists kategori_hapus on public.categories;
create policy kategori_hapus on public.categories
    for delete
    using (household_id is not null and private.household_role(household_id) in ('ayah', 'ibu'));

-- 4. Seed 8 kategori sistem (sama dengan src/data/mockData.js)
insert into public.categories (household_id, name, kind, icon, color, is_system) values
    (null, 'Makanan & Minuman',  'expense', '🍽️', '#F59E0B', true),
    (null, 'Transportasi',       'expense', '🚗', '#3B82F6', true),
    (null, 'Belanja',            'expense', '🛍️', '#EC4899', true),
    (null, 'Pendidikan',         'expense', '📚', '#8B5CF6', true),
    (null, 'Kesehatan',          'expense', '💊', '#10B981', true),
    (null, 'Tagihan & Utilitas', 'expense', '💡', '#F97316', true),
    (null, 'Hiburan',            'expense', '🎬', '#06B6D4', true),
    (null, 'Lainnya',            'income',  '📦', '#94A3B8', true)
on conflict do nothing;
