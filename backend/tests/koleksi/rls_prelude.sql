-- tiruan skema auth Supabase (auth.users, auth.uid) untuk uji migrasi di PostgreSQL lokal
-- Penulis: Gilang Nur Adha
create schema if not exists auth;
create table if not exists auth.users (id uuid primary key, email text, raw_user_meta_data jsonb default '{}');
create or replace function auth.uid() returns uuid language sql stable as
$$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
do $$ begin create role authenticated; exception when duplicate_object then null; end $$;
do $$ begin create domain citext as text; exception when duplicate_object then null; end $$;
