create schema if not exists extensions;
create extension if not exists pgcrypto with schema extensions;

create type public.memo_status as enum (
  'draft',
  'screening',
  'diligence',
  'approved',
  'declined'
);

create type public.signal_kind as enum (
  'traction',
  'founder',
  'market',
  'competitive',
  'risk'
);

create table public.founders (
  id uuid primary key default extensions.gen_random_uuid(),
  user_id uuid,
  full_name text not null,
  email text not null,
  company_name text not null,
  linkedin_url text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (email, company_name)
);

create table public.memos (
  id uuid primary key default extensions.gen_random_uuid(),
  founder_id uuid not null references public.founders(id) on delete cascade,
  title text not null,
  thesis text not null default '',
  recommendation text,
  status public.memo_status not null default 'draft',
  score numeric(5, 2) check (score between 0 and 100),
  audio_storage_path text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.signals (
  id uuid primary key default extensions.gen_random_uuid(),
  founder_id uuid not null references public.founders(id) on delete cascade,
  memo_id uuid references public.memos(id) on delete cascade,
  kind public.signal_kind not null,
  source_url text,
  summary text not null,
  confidence numeric(4, 3) not null default 0.5 check (confidence between 0 and 1),
  observed_at timestamptz not null default now(),
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index founders_user_id_idx on public.founders(user_id);
create index memos_founder_id_idx on public.memos(founder_id);
create index signals_founder_id_idx on public.signals(founder_id);
create index signals_memo_id_idx on public.signals(memo_id);
create index signals_observed_at_idx on public.signals(observed_at desc);

alter table public.founders enable row level security;
alter table public.memos enable row level security;
alter table public.signals enable row level security;

create policy "founders_select_own"
on public.founders for select
to authenticated
using (user_id = (select auth.uid()));

create policy "founders_insert_own"
on public.founders for insert
to authenticated
with check (user_id = (select auth.uid()));

create policy "memos_select_for_founder"
on public.memos for select
to authenticated
using (
  exists (
    select 1 from public.founders
    where founders.id = memos.founder_id
      and founders.user_id = (select auth.uid())
  )
);

create policy "signals_select_for_founder"
on public.signals for select
to authenticated
using (
  exists (
    select 1 from public.founders
    where founders.id = signals.founder_id
      and founders.user_id = (select auth.uid())
  )
);

grant select, insert, update on public.founders to authenticated;
grant select on public.memos, public.signals to authenticated;
grant all on public.founders, public.memos, public.signals to service_role;

comment on table public.founders is 'Founder identity and company context for a deal.';
comment on table public.memos is 'Versionable investment recommendation output.';
comment on table public.signals is 'Source-backed evidence gathered during sourcing and diligence.';
