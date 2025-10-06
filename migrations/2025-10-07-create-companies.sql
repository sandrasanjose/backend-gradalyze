-- Create companies table for vector/RIASEC-based recommendations
-- Features:
-- - riasec_weights: [realistic, investigative, artistic, social, enterprising, conventional] (0..1)
-- - skills_vector: [programming, data, systems, ux, management, comms] (0..1)
-- - roles: free-form role tags used for filtering (e.g., {"Software Engineer","Data"})

create table if not exists public.companies (
  id bigserial primary key,
  name text not null unique,
  website text,
  locations text[] default '{}'::text[],
  roles text[] default '{}'::text[],
  riasec_weights numeric[] not null default '{0,0,0,0,0,0}'::numeric[],
  skills_vector numeric[] not null default '{0,0,0,0,0,0}'::numeric[],
  description text default '',
  source text default 'seed',
  active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- Keep arrays length at 6 for our math (defensive check)
alter table public.companies
  add constraint companies_riasec_len check (array_length(riasec_weights, 1) = 6),
  add constraint companies_skills_len check (array_length(skills_vector, 1) = 6);

-- Helpful indexes
create index if not exists idx_companies_active on public.companies(active);
create index if not exists idx_companies_roles on public.companies using gin(roles);
create index if not exists idx_companies_locations on public.companies using gin(locations);

-- Trigger to keep updated_at fresh
create or replace function public.set_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at := now();
  return new;
end; $$;

drop trigger if exists trg_companies_updated_at on public.companies;
create trigger trg_companies_updated_at
before update on public.companies
for each row execute function public.set_updated_at();

-- No seed data by request; populate via admin tools or ingestion.


