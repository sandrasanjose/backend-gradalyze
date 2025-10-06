-- Add denormalized career forecast columns for top-6 careers
-- We do NOT store JSON for forecast; these numeric columns are the source of truth

alter table if exists public.users
  add column if not exists career_forecast_analyzed_at timestamptz,
  add column if not exists career_top_jobs text[] default '{}'::text[],
  add column if not exists career_top_jobs_scores numeric[] default '{}'::numeric[],
  add column if not exists job_recommendations jsonb;

comment on column public.users.career_top_jobs is 'Top 6 recommended jobs as text array, ordered by fit';
comment on column public.users.career_top_jobs_scores is 'Scores (0..1) corresponding to career_top_jobs in the same order';
comment on column public.users.job_recommendations is 'Stored job/company recommendations payload (JSON)';


