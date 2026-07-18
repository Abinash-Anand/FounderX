\set db_password `echo "$POSTGRES_PASSWORD"`

select format('create role supabase_admin nologin superuser createdb createrole replication bypassrls')
where not exists (select 1 from pg_roles where rolname = 'supabase_admin') \gexec

select format('create role anon nologin noinherit')
where not exists (select 1 from pg_roles where rolname = 'anon') \gexec

select format('create role authenticated nologin noinherit')
where not exists (select 1 from pg_roles where rolname = 'authenticated') \gexec

select format('create role service_role nologin noinherit bypassrls')
where not exists (select 1 from pg_roles where rolname = 'service_role') \gexec

select format('create role authenticator login noinherit password %L', :'db_password')
where not exists (select 1 from pg_roles where rolname = 'authenticator') \gexec

select format('create role supabase_auth_admin login noinherit createrole password %L', :'db_password')
where not exists (select 1 from pg_roles where rolname = 'supabase_auth_admin') \gexec

select format('create role supabase_storage_admin login noinherit createrole password %L', :'db_password')
where not exists (select 1 from pg_roles where rolname = 'supabase_storage_admin') \gexec

alter role authenticator password :'db_password';
alter role supabase_auth_admin password :'db_password';
alter role supabase_storage_admin password :'db_password';

grant anon, authenticated, service_role to authenticator;
grant anon, authenticated, service_role to supabase_storage_admin;
grant all privileges on database postgres to supabase_auth_admin;
grant all privileges on database postgres to supabase_storage_admin;

create schema if not exists auth authorization supabase_auth_admin;
create schema if not exists storage authorization supabase_storage_admin;
alter role supabase_auth_admin set search_path = auth;
alter role supabase_storage_admin set search_path = storage;
grant all on schema auth to supabase_auth_admin;
grant all on schema storage to supabase_storage_admin;
grant create on schema public to supabase_auth_admin, supabase_storage_admin;
grant usage on schema public to anon, authenticated, service_role;
grant usage on schema storage to anon, authenticated, service_role;
alter default privileges for role supabase_storage_admin in schema storage
  grant select, insert, update, delete on tables to anon, authenticated, service_role;
alter default privileges for role supabase_storage_admin in schema storage
  grant usage, select on sequences to anon, authenticated, service_role;

create or replace function auth.uid()
returns uuid
language sql
stable
as $$
  select coalesce(
    nullif(current_setting('request.jwt.claim.sub', true), ''),
    nullif(current_setting('request.jwt.claims', true), '')::jsonb ->> 'sub'
  )::uuid
$$;
alter function auth.uid() owner to supabase_auth_admin;
