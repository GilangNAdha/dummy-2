-- ============================================================
-- Migrasi tabel accounts (dompet: rekening bank, tunai, e-wallet)
-- Penulis: Gilang Nur Adha
-- Dipasang setelah households dan household_members (0002, 0003)
-- Tidak menyimpan nomor rekening, nomor kartu, atau PIN.
-- Saldo berjalan TIDAK disimpan, dihitung backend saat dibaca (current_balance).
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
    household_id    uuid not null references public.households(id) on delete restrict,
    name            varchar(80) not null,
    type            account_type not null,
    provider        varchar(60),
    opening_balance bigint not null default 0,
    is_active       boolean not null default true,
    created_at      timestamptz not null default now(),
    updated_at      timestamptz not null default now()
);

-- nama dompet unik per rumah tangga (aturan integritas 34)
create unique index if not exists uq_accounts_household_name
    on public.accounts (household_id, name);

create index if not exists idx_accounts_household
    on public.accounts (household_id);

-- 3. Fungsi trigger updated_at bersama (create or replace agar aman bentrok)
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

-- 4. RLS: anggota boleh baca, hanya ayah dan ibu boleh tulis
alter table public.accounts enable row level security;

drop policy if exists dompet_baca_anggota on public.accounts;
create policy dompet_baca_anggota on public.accounts
    for select
    using (
        household_id in (
            select household_id from public.household_members
            where user_id = auth.uid()
        )
    );

drop policy if exists dompet_tulis_ayah_ibu on public.accounts;
create policy dompet_tulis_ayah_ibu on public.accounts
    for all
    using (
        household_id in (
            select household_id from public.household_members
            where user_id = auth.uid() and role in ('ayah', 'ibu')
        )
    )
    with check (
        household_id in (
            select household_id from public.household_members
            where user_id = auth.uid() and role in ('ayah', 'ibu')
        )
    );
