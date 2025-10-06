-- Add optional logo fields for companies (URL or storage path)
alter table if exists public.companies
  add column if not exists logo_url text,
  add column if not exists logo_storage_path text;

comment on column public.companies.logo_url is 'Public URL to company logo (if available)';
comment on column public.companies.logo_storage_path is 'Supabase storage path to logo (if managed via storage)';


