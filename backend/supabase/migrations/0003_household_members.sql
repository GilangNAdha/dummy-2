-- ============================================================
-- Migrasi tabel household_members (anggota rumah tangga)
-- Penulis: Nizar Hermawan
-- ============================================================

-- 1. Buat skema private untuk fungsi bantu RLS
create schema if not exists private;
revoke all on schema private from public;

-- 2. Enum peran anggota
do $$ begin
    create type member_role as enum ('ayah', 'ibu', 'anak');
exception
    when duplicate_object then null;
end $$;

-- 3. Tabel household_members
create table if not exists public.household_members (
    id                 uuid primary key default gen_random_uuid(),
    household_id       uuid not null references public.households(id) on delete cascade,
    user_id            uuid not null references auth.users(id) on delete cascade,
    role               member_role not null,
    display_name       varchar(60) not null,
    can_approve_budget boolean not null default false,
    joined_at          timestamptz not null default now(),
    unique (household_id, user_id)
);

create index if not exists idx_household_members_user
    on public.household_members (user_id);

alter table public.household_members enable row level security;

-- ------------------------------------------------------------
-- Fungsi bantu RLS (Dipindah ke skema private)
-- ------------------------------------------------------------
create or replace function private.is_household_member(p_household_id uuid)
returns boolean
language sql
stable
security definer
set search_path = public
as $$
    select exists (
        select 1 from public.household_members
        where household_id = p_household_id
          and user_id = auth.uid()
    );
$$;

create or replace function private.household_role(p_household_id uuid)
returns member_role
language sql
stable
security definer
set search_path = public
as $$
    select role from public.household_members
    where household_id = p_household_id
      and user_id = auth.uid()
    limit 1;
$$;

-- ------------------------------------------------------------
-- Kebijakan household_members
-- ------------------------------------------------------------
drop policy if exists anggota_baca on public.household_members;
create policy anggota_baca on public.household_members
    for select
    using (private.is_household_member(household_id));

drop policy if exists anggota_tambah on public.household_members;
create policy anggota_tambah on public.household_members
    for insert
    with check (private.household_role(household_id) = 'ayah');

drop policy if exists anggota_ubah on public.household_members;
create policy anggota_ubah on public.household_members
    for update
    using (private.household_role(household_id) = 'ayah')
    with check (private.household_role(household_id) = 'ayah');

drop policy if exists anggota_hapus on public.household_members;
create policy anggota_hapus on public.household_members
    for delete
    using (private.household_role(household_id) = 'ayah');

-- ------------------------------------------------------------
-- Kebijakan households
-- ------------------------------------------------------------
drop policy if exists rumah_baca on public.households;
create policy rumah_baca on public.households
    for select
    using (owner_user_id = auth.uid() or private.is_household_member(id));

drop policy if exists rumah_tambah on public.households;
create policy rumah_tambah on public.households
    for insert
    with check (owner_user_id = auth.uid());

drop policy if exists rumah_ubah on public.households;
create policy rumah_ubah on public.households
    for update
    using (private.household_role(id) = 'ayah')
    with check (private.household_role(id) = 'ayah');

-- ------------------------------------------------------------
-- Trigger otomatis: Pembuat rumah tangga jadi anggota 'ayah'
-- ------------------------------------------------------------
create or replace function public.tambah_pemilik_sebagai_ayah()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
    insert into public.household_members
        (household_id, user_id, role, display_name, can_approve_budget)
    values (
        new.id,
        new.owner_user_id,
        'ayah',
        coalesce((select full_name from public.profiles where id = new.owner_user_id), 'Ayah'),
        true
    )
    on conflict (household_id, user_id) do nothing;
    return new;
end;
$$;

drop trigger if exists trg_tambah_pemilik_sebagai_ayah on public.households;
create trigger trg_tambah_pemilik_sebagai_ayah
    after insert on public.households
    for each row execute function public.tambah_pemilik_sebagai_ayah();

    