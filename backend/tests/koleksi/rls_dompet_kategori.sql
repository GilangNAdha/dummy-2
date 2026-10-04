-- uji migrasi 0004/0005 dan RLS lintas rumah tangga di PostgreSQL lokal
-- Penulis: Gilang Nur Adha
-- Jalankan setelah rls_prelude.sql dan migrasi 0001-0005, lihat docs/DOMPET_DAN_KATEGORI.md
\set ON_ERROR_STOP 0
\set ayah '11111111-1111-1111-1111-111111111111'
\set anak '22222222-2222-2222-2222-222222222222'
\set lain '33333333-3333-3333-3333-333333333333'
insert into auth.users(id,email) values (:'ayah','a@x'),(:'anak','c@x'),(:'lain','l@x') on conflict do nothing;
insert into households(id,name,owner_user_id) values ('aaaaaaaa-0000-0000-0000-000000000001','Keluarga Santoso',:'ayah'),('aaaaaaaa-0000-0000-0000-000000000002','Keluarga Lain',:'lain') on conflict do nothing;
insert into household_members(household_id,user_id,role,display_name) values ('aaaaaaaa-0000-0000-0000-000000000001',:'anak','anak','Anak') on conflict do nothing;
\i supabase/seed.sql
\i supabase/seed.sql
select 'kategori_sistem=' || count(*) from categories where is_system;
select 'dompet_seed=' || count(*) from accounts;
select 'rls=' || string_agg(relname||':'||relrowsecurity, ',') from pg_class where relname in ('accounts','categories');
select 'policies=' || count(*) from pg_policies where tablename in ('accounts','categories');
\echo '-- harus gagal: nama ganda, warna salah, sistem ganda, sistem dengan household'
insert into accounts(household_id,name,type) values ('aaaaaaaa-0000-0000-0000-000000000001','Tunai','cash');
insert into categories(household_id,name,kind,color) values ('aaaaaaaa-0000-0000-0000-000000000001','X','expense','merah');
insert into categories(household_id,name,kind,is_system) values (null,'Gaji','income',true);
insert into categories(household_id,name,kind,is_system) values ('aaaaaaaa-0000-0000-0000-000000000001','Y','income',true);
\echo '-- harus gagal: hapus rumah tangga yang punya dompet (RESTRICT)'
delete from households where name='Keluarga Santoso';
grant usage on schema public, private, auth to authenticated;
grant all on all tables in schema public to authenticated;
grant execute on all functions in schema private to authenticated;
set role authenticated;
select set_config('request.jwt.claim.sub', :'lain', false);
select 'lain_lihat_dompet=' || count(*) from accounts;
select 'lain_lihat_kategori=' || count(*) from categories;
select set_config('request.jwt.claim.sub', :'anak', false);
select 'anak_lihat_dompet=' || count(*) from accounts;
\echo '-- harus gagal: anak insert dompet / kategori'
insert into accounts(household_id,name,type) values ('aaaaaaaa-0000-0000-0000-000000000001','OVO','ewallet');
insert into categories(household_id,name,kind) values ('aaaaaaaa-0000-0000-0000-000000000001','Jajan','expense');
with t as (update accounts set name='Z' where name='Tunai' returning 1) select 'anak_update_baris=' || count(*) from t;
select set_config('request.jwt.claim.sub', :'ayah', false);
insert into categories(household_id,name,kind) values ('aaaaaaaa-0000-0000-0000-000000000001','Arisan','expense');
with t as (update categories set name='Q' where is_system returning 1) select 'ayah_ubah_sistem=' || count(*) from t;
with t as (update categories set color='#000000' where name='Arisan' returning 1) select 'ayah_ubah_milik=' || count(*) from t;
select 'updated_at_berubah=' || (updated_at > created_at) from categories where name='Arisan';
