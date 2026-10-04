-- ============================================================
-- Migrasi tabel accounts (dompet: rekening bank, tunai, e-wallet)
-- Penulis: Gilang Nur Adha
-- Dipasang setelah households dan household_members (0002, 0003)
-- Catatan: hanya nama dompet, TIDAK menyimpan nomor rekening atau kredensial bank.
-- ============================================================

-- 1. Enum jenis dompet
do $$ begin
    create type account_type as enum ('bank', 'cash', 'ewallet');
exception
    when duplicate_object then null;
end $$;

-- 2. Tabel accounts
create table if not exists public.accounts (
    id              uuid primary key default gen_random_uuid(),
    household_id    uuid not null references public.households(id) on delete cascade,
    name            varchar(60) not null,
    type            account_type not null default 'cash',
    icon            varchar(8),
    opening_balance bigint not null default 0 check (opening_balance >= 0),
    is_archived     boolean not null default false,
    created_at      timestamptz not null default now(),
    updated_at      timestamptz not null default now()
);

-- nama dompet unik di dalam satu rumah tangga
create unique index if not exists uq_accounts_household_name
    on public.accounts (household_id, name);

-- 3. Pemicu updated_at (dipakai juga oleh tabel categories)
create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

drop trigger if exists trg_accounts_updated_at on public.accounts;
create trigger trg_accounts_updated_at
    before update on public.accounts
    for each row execute function public.set_updated_at();

-- 4. RLS: semua anggota boleh membaca, hanya Ayah dan Ibu boleh menulis
alter table public.accounts enable row level security;

drop policy if exists dompet_baca on public.accounts;
create policy dompet_baca on public.accounts
    for select
    using (private.is_household_member(household_id));

drop policy if exists dompet_tambah on public.accounts;
create policy dompet_tambah on public.accounts
    for insert
    with check (private.household_role(household_id) in ('ayah', 'ibu'));

drop policy if exists dompet_ubah on public.accounts;
create policy dompet_ubah on public.accounts
    for update
    using (private.household_role(household_id) in ('ayah', 'ibu'))
    with check (private.household_role(household_id) in ('ayah', 'ibu'));

drop policy if exists dompet_hapus on public.accounts;
create policy dompet_hapus on public.accounts
    for delete
    using (private.household_role(household_id) in ('ayah', 'ibu'));
