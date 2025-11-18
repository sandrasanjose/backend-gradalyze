-- Migration script for creating academic_records and analysis_results tables
-- Run this in your Supabase SQL Editor

-- Create academic_records table
CREATE TABLE IF NOT EXISTS academic_records (
    record_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    sub_code TEXT,
    sub_name TEXT NOT NULL,
    units DECIMAL NOT NULL,
    grades DECIMAL NOT NULL,
    year INTEGER,
    semester TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for faster queries by user_id
CREATE INDEX IF NOT EXISTS idx_academic_records_user_id ON academic_records(user_id);
CREATE INDEX IF NOT EXISTS idx_academic_records_semester ON academic_records(user_id, year, semester);

-- Create analysis_results table
CREATE TABLE IF NOT EXISTS analysis_results (
    analysis_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    primary_archetype TEXT,
    archetype_realistic_perc DECIMAL,
    archetype_investigative_perc DECIMAL,
    archetype_artistic_perc DECIMAL,
    archetype_social_perc DECIMAL,
    archetype_enterprising_perc DECIMAL,
    archetype_conventional_perc DECIMAL,
    career_top_jobs JSONB,
    career_top_job_scores JSONB,
    job_recommendations JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for faster queries by user_id
CREATE INDEX IF NOT EXISTS idx_analysis_results_user_id ON analysis_results(user_id);
CREATE INDEX IF NOT EXISTS idx_analysis_results_created_at ON analysis_results(created_at DESC);

-- Create trigger to update updated_at timestamp for academic_records
CREATE OR REPLACE FUNCTION update_academic_records_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_academic_records_updated_at
    BEFORE UPDATE ON academic_records
    FOR EACH ROW
    EXECUTE FUNCTION update_academic_records_updated_at();

-- Create trigger to update updated_at timestamp for analysis_results
CREATE OR REPLACE FUNCTION update_analysis_results_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_analysis_results_updated_at
    BEFORE UPDATE ON analysis_results
    FOR EACH ROW
    EXECUTE FUNCTION update_analysis_results_updated_at();

-- Enable Row Level Security (RLS)
ALTER TABLE academic_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE analysis_results ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for academic_records
-- Allow users to read their own records
CREATE POLICY "Users can view their own academic records"
    ON academic_records FOR SELECT
    USING (auth.uid()::text = user_id::text);

-- Allow users to insert their own records
CREATE POLICY "Users can insert their own academic records"
    ON academic_records FOR INSERT
    WITH CHECK (auth.uid()::text = user_id::text);

-- Allow users to update their own records
CREATE POLICY "Users can update their own academic records"
    ON academic_records FOR UPDATE
    USING (auth.uid()::text = user_id::text);

-- Allow users to delete their own records
CREATE POLICY "Users can delete their own academic records"
    ON academic_records FOR DELETE
    USING (auth.uid()::text = user_id::text);

-- Create RLS policies for analysis_results
-- Allow users to read their own analysis results
CREATE POLICY "Users can view their own analysis results"
    ON analysis_results FOR SELECT
    USING (auth.uid()::text = user_id::text);

-- Allow users to insert their own analysis results
CREATE POLICY "Users can insert their own analysis results"
    ON analysis_results FOR INSERT
    WITH CHECK (auth.uid()::text = user_id::text);

-- Allow users to update their own analysis results
CREATE POLICY "Users can update their own analysis results"
    ON analysis_results FOR UPDATE
    USING (auth.uid()::text = user_id::text);

-- Allow users to delete their own analysis results
CREATE POLICY "Users can delete their own analysis results"
    ON analysis_results FOR DELETE
    USING (auth.uid()::text = user_id::text);

-- Grant permissions (if using service role key, these may not be necessary)
-- GRANT ALL ON academic_records TO authenticated;
-- GRANT ALL ON analysis_results TO authenticated;
-- GRANT USAGE, SELECT ON SEQUENCE academic_records_record_id_seq TO authenticated;
-- GRANT USAGE, SELECT ON SEQUENCE analysis_results_analysis_id_seq TO authenticated;
