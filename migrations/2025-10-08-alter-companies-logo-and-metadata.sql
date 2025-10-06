-- Simplify companies branding to URL-only and add optional metadata
alter table if exists public.companies
  drop column if exists logo_storage_path,
  add column if not exists logo_url text,
  
 
