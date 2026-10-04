-- tabel profil pengguna, pelengkap tabel bawaan auth.users
create extension if not exists citext;

create table if not exists public.profiles (
    id            uuid primary key references auth.users(id) on delete cascade,
    email         citext not null,
    full_name     varchar(120) not null,
    avatar_emoji  varchar(8),
    last_login_at timestamptz,
    created_at    timestamptz not null default now()
);

create index if not exists idx_profiles_email on public.profiles (email);

alter table public.profiles enable row level security;

drop policy if exists profil_baca_sendiri on public.profiles;
create policy profil_baca_sendiri on public.profiles
    for select
    using (id = auth.uid());

drop policy if exists profil_ubah_sendiri on public.profiles;
create policy profil_ubah_sendiri on public.profiles
    for update
    using (id = auth.uid())
    with check (id = auth.uid());

drop policy if exists profil_tambah_sendiri on public.profiles;
create policy profil_tambah_sendiri on public.profiles
    for insert
    with check (id = auth.uid());

-- profil dibuat otomatis setelah pendaftaran
create or replace function public.buat_profil_baru()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
    insert into public.profiles (id, email, full_name, avatar_emoji)
    values (
        new.id,
        new.email,
        coalesce(new.raw_user_meta_data ->> 'full_name', new.email),
        new.raw_user_meta_data ->> 'avatar_emoji'
    )
    on conflict (id) do nothing;
    return new;
end;
$$;

drop trigger if exists trg_buat_profil_baru on auth.users;
create trigger trg_buat_profil_baru
    after insert on auth.users
    for each row execute function public.buat_profil_baru();
