-- ============================================================
-- Migrasi tabel goal_contributions (riwayat setoran tujuan)
-- Penulis: Arjuna Rangga Lengkey
-- Penomoran dan kolom dirapikan oleh Chandra TW, 30 September 2026
-- Dipasang setelah migrasi tabel goals, accounts, dan transactions
-- ============================================================

create table if not exists public.goal_contributions (
    id             uuid primary key default gen_random_uuid(),
    goal_id        uuid not null references public.goals(id) on delete cascade,
    member_id      uuid not null references public.household_members(id) on delete restrict,
    account_id     uuid references public.accounts(id) on delete set null,
    transaction_id uuid references public.transactions(id) on delete set null,
    amount         bigint not null check (amount > 0),
    contributed_at timestamptz not null default now(),
    created_at     timestamptz not null default now()
);

create index if not exists idx_goal_contributions_goal on public.goal_contributions (goal_id);

-- kebijakan akses, mengikuti rumah tangga pemilik tujuan
alter table public.goal_contributions enable row level security;

drop policy if exists goal_contributions_household_policy on public.goal_contributions;
create policy goal_contributions_household_policy on public.goal_contributions
    for all
    using (
        goal_id in (
            select id from public.goals
            where household_id in (
                select household_id from public.household_members
                where user_id = auth.uid()
            )
        )
    )
    with check (
        goal_id in (
            select id from public.goals
            where household_id in (
                select household_id from public.household_members
                where user_id = auth.uid()
            )
        )
    );
