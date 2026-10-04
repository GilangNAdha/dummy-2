-- ============================================================
-- Migrasi tabel goals (tujuan tabungan)
-- Penulis: Arjuna Rangga Lengkey
-- Penomoran dan kolom dirapikan oleh Chandra TW, 30 September 2026
-- Dipasang setelah migrasi tabel households dan household_members
-- ============================================================

-- tipe keadaan tujuan
do $$ begin
    create type goal_status as enum ('active', 'achieved', 'archived');
exception
    when duplicate_object then null;
end $$;

create table if not exists public.goals (
    id            uuid primary key default gen_random_uuid(),
    household_id  uuid not null references public.households(id) on delete cascade,
    name          varchar(120) not null,
    target_amount bigint not null check (target_amount > 0),
    deadline      date,
    icon          varchar(8),
    color         char(7) not null default '#10B981',
    status        goal_status not null default 'active',
    created_at    timestamptz not null default now()
);

create index if not exists idx_goals_household on public.goals (household_id);

-- kebijakan akses, hanya anggota rumah tangga pemilik tujuan
alter table public.goals enable row level security;

drop policy if exists goals_household_policy on public.goals;
create policy goals_household_policy on public.goals
    for all
    using (
        household_id in (
            select household_id from public.household_members
            where user_id = auth.uid()
        )
    )
    with check (
        household_id in (
            select household_id from public.household_members
            where user_id = auth.uid()
        )
    );
