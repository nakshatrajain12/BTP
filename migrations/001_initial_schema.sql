-- Bronze Layer
CREATE TABLE IF NOT EXISTS schemes_raw (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scraped_at TIMESTAMPTZ DEFAULT NOW(),
    source_url TEXT NOT NULL,
    raw_content JSONB NOT NULL,
    content_hash TEXT NOT NULL
);

-- Silver Layer
CREATE TABLE IF NOT EXISTS schemes_clean (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scheme_name TEXT NOT NULL,
    ministry TEXT NOT NULL,
    launch_year INTEGER,
    status TEXT,
    category TEXT,
    source_url TEXT,
    funding_type TEXT,
    max_funding_amount BIGINT,
    total_budget_allocated BIGINT,
    startups_funded_count INTEGER,
    sector_eligibility TEXT[],
    startup_stage TEXT[],
    dpiit_required BOOLEAN,
    geographic_restriction TEXT,
    application_portal TEXT,
    application_deadline DATE,
    processing_timeline TEXT,
    required_documents TEXT[],
    success_stories TEXT,
    sector_distribution JSONB,
    nlp_summary TEXT,
    content_hash TEXT,
    last_scraped_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_summarised_hash TEXT,
    UNIQUE(scheme_name, ministry)
);

-- Recommendation Cache
CREATE TABLE IF NOT EXISTS recommendation_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sector TEXT NOT NULL,
    stage TEXT NOT NULL,
    state TEXT NOT NULL DEFAULT '',
    recommendations JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(sector, stage, state)
);
