# Database Migrations

This directory contains SQL migration scripts for the Gradalyze database.

## New Tables

### academic_records
Stores student academic records with grades and course information.

**Columns:**
- `record_id` (SERIAL PRIMARY KEY) - Auto-incrementing record ID
- `user_id` (INTEGER, FK to users.user_id) - Reference to the user
- `sub_code` (TEXT) - Subject code (optional)
- `sub_name` (TEXT NOT NULL) - Subject name
- `units` (DECIMAL NOT NULL) - Course units/credits
- `grades` (DECIMAL NOT NULL) - Grade received
- `year` (INTEGER) - Academic year
- `semester` (TEXT) - Semester (e.g., "1st Semester", "2nd Semester")
- `created_at` (TIMESTAMP) - Record creation timestamp
- `updated_at` (TIMESTAMP) - Last update timestamp

### analysis_results
Stores career analysis results including RIASEC archetypes and job recommendations.

**Columns:**
- `analysis_id` (SERIAL PRIMARY KEY) - Auto-incrementing analysis ID
- `user_id` (INTEGER, FK to users.user_id) - Reference to the user
- `primary_archetype` (TEXT) - Primary RIASEC archetype
- `archetype_realistic_perc` (DECIMAL) - Realistic archetype percentage
- `archetype_investigative_perc` (DECIMAL) - Investigative archetype percentage
- `archetype_artistic_perc` (DECIMAL) - Artistic archetype percentage
- `archetype_social_perc` (DECIMAL) - Social archetype percentage
- `archetype_enterprising_perc` (DECIMAL) - Enterprising archetype percentage
- `archetype_conventional_perc` (DECIMAL) - Conventional archetype percentage
- `career_top_jobs` (JSONB) - Array of top job recommendations
- `career_top_job_scores` (JSONB) - Array of scores for top jobs
- `job_recommendations` (JSONB) - Detailed job recommendations object
- `created_at` (TIMESTAMP) - Analysis creation timestamp
- `updated_at` (TIMESTAMP) - Last update timestamp

## Running Migrations

1. Open your Supabase project dashboard
2. Navigate to the SQL Editor
3. Copy the contents of `create_new_tables.sql`
4. Paste and execute the SQL script

## API Endpoints

### Academic Records
- `GET /api/academic-records/?user_id={id}` - Get all records for a user
- `GET /api/academic-records/{record_id}` - Get specific record
- `POST /api/academic-records/` - Create new record
- `POST /api/academic-records/bulk` - Create multiple records
- `PUT /api/academic-records/{record_id}` - Update record
- `DELETE /api/academic-records/{record_id}` - Delete record
- `DELETE /api/academic-records/user/{user_id}` - Delete all user records
- `GET /api/academic-records/semester?user_id={id}&year={year}&semester={sem}` - Get semester records

### Analysis Results
- `GET /api/analysis-results/?user_id={id}` - Get latest analysis for user
- `GET /api/analysis-results/history?user_id={id}` - Get all analyses for user
- `GET /api/analysis-results/{analysis_id}` - Get specific analysis
- `POST /api/analysis-results/` - Create new analysis
- `POST /api/analysis-results/upsert` - Create or update analysis
- `PUT /api/analysis-results/{analysis_id}` - Update analysis
- `DELETE /api/analysis-results/{analysis_id}` - Delete analysis
- `DELETE /api/analysis-results/user/{user_id}` - Delete all user analyses

## Python Models

The models are located in `app/models/`:
- `academic_records.py` - AcademicRecord model
- `analysis_results.py` - AnalysisResult model

Both models provide class methods for CRUD operations:
- `create()` - Insert new record
- `get_by_user_id()` - Fetch by user
- `get_by_id()` - Fetch by ID
- `update()` - Update record
- `delete()` - Delete record

## Notes

- Both tables use foreign keys to the `users` table with CASCADE delete
- Row Level Security (RLS) is enabled for data protection
- Indexes are created for optimized queries
- Timestamps are automatically managed with triggers
