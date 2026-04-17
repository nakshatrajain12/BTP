-- This table stores persisted user profiles linked strictly to Supabase Auth
CREATE TABLE startup_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    company_name TEXT NOT NULL,
    sector TEXT NOT NULL,
    stage TEXT NOT NULL,
    geographic_restriction TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_login TIMESTAMPTZ DEFAULT NOW()
);

-- Turn on Row Level Security so users can only see their own profile
ALTER TABLE startup_profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own profile" 
    ON startup_profiles FOR SELECT 
    USING (auth.uid() = id);

CREATE POLICY "Users can insert own profile" 
    ON startup_profiles FOR INSERT 
    WITH CHECK (auth.uid() = id);

CREATE POLICY "Users can update own profile" 
    ON startup_profiles FOR UPDATE 
    USING (auth.uid() = id);
