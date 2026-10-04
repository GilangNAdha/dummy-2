-- ============================================================
-- Migrasi tabel households (rumah tangga)
-- Penulis: Nizar Hermawan
-- ============================================================

create table if not exists public.households (
    id                uuid primary key default gen_random_uuid(),
    name              varchar(120) not null,
    currency          char(3) not null default 'IDR',
    monthly_start_day smallint not null default 1
                      check (monthly_start_day between 1 and 28),
    owner_user_id     uuid not null references auth.users(id) on delete restrict,
    created_at        timestamptz not null default now(),
    deleted_at        timestamptz
);

create index if not exists idx_households_owner
    on public.households (owner_user_id)
    where deleted_at is null;

alter table public.households enable row level security;

