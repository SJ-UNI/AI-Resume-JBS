-- Tables for Resume Match AI application

-- 1. Table for all analysis sessions (parent analysis)
CREATE TABLE IF NOT EXISTS public.analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    job_title TEXT NOT NULL,
    analysis_type TEXT NOT NULL, -- 'single' or 'bulk'
    total_resumes INTEGER DEFAULT 1,
    avg_score FLOAT DEFAULT 0,
    job_description TEXT,
    job_skills TEXT[]
);

-- 2. Table for each candidate in an analysis
CREATE TABLE IF NOT EXISTS public.candidates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id UUID REFERENCES public.analyses(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    name TEXT NOT NULL,
    score FLOAT NOT NULL,
    semantic_score FLOAT,
    skill_score FLOAT,
    experience_years INTEGER,
    matched_skills TEXT[],
    missing_skills TEXT[],
    skill_match_percentage FLOAT,
    suggestions TEXT[],
    key_strengths TEXT[],
    areas_for_improvement TEXT[]
);

-- 3. Table for aggregated skill statistics
CREATE TABLE IF NOT EXISTS public.skill_stats (
    skill_name TEXT PRIMARY KEY,
    match_count INTEGER DEFAULT 0,
    miss_count INTEGER DEFAULT 0,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Disable RLS for demo/dev (allows public read-write without policies)
ALTER TABLE public.analyses DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.candidates DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.skill_stats DISABLE ROW LEVEL SECURITY;
