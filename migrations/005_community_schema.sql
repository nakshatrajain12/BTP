-- 1. Community Discussion Posts
CREATE TABLE community_posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    author_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    author_name TEXT NOT NULL,
    company_name TEXT DEFAULT 'Founder',
    category TEXT NOT NULL CHECK (category IN ('Grants', 'DPIIT Recognition', 'Compliance', 'Investor Pitch', 'General')),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    upvotes INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Post Replies
CREATE TABLE community_replies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    post_id UUID REFERENCES community_posts(id) ON DELETE CASCADE,
    author_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    author_name TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Policy & Scheme Advisors
CREATE TABLE advisors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    role_title TEXT NOT NULL,
    organization TEXT NOT NULL,
    expertise TEXT[] NOT NULL,
    bio TEXT NOT NULL,
    linkedin_url TEXT,
    contact_email TEXT,
    is_verified BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable Row Level Security (RLS)
ALTER TABLE community_posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE community_replies ENABLE ROW LEVEL SECURITY;
ALTER TABLE advisors ENABLE ROW LEVEL SECURITY;

-- Post Policies
CREATE POLICY "Public read community_posts" 
    ON community_posts FOR SELECT USING (true);

CREATE POLICY "Authenticated users can create posts" 
    ON community_posts FOR INSERT WITH CHECK (auth.uid() = author_id);

CREATE POLICY "Authors can update own posts" 
    ON community_posts FOR UPDATE USING (auth.uid() = author_id);

CREATE POLICY "Authors can delete own posts" 
    ON community_posts FOR DELETE USING (auth.uid() = author_id);

-- Reply Policies
CREATE POLICY "Public read community_replies" 
    ON community_replies FOR SELECT USING (true);

CREATE POLICY "Authenticated users can reply" 
    ON community_replies FOR INSERT WITH CHECK (auth.uid() = author_id);

-- Advisor Directory Policies
CREATE POLICY "Public read advisors" 
    ON advisors FOR SELECT USING (true);

-- Seed Initial Advisors
INSERT INTO advisors (name, role_title, organization, expertise, bio, linkedin_url, contact_email)
VALUES
('Dr. Ramesh Sundaram', 'Senior Policy Consultant', 'Startup India Advisory Panel', ARRAY['DPIIT Section 80-IAC', 'Seed Fund Scheme', 'Tax Exemption'], 'Former advisor to DPIIT helping deep-tech startups navigate seed funding and angel tax exemption.', 'https://linkedin.com', 'advisor@policyradar.in'),
('Priya Venkat', 'Grant Specialist', 'BioNEST / BIRAC Mentor', ARRAY['BIRAC BIG', 'Biotech Grants', 'Clinical Trials Compliance'], 'Assists early-stage life sciences and medtech startups in writing winning BIRAC grant proposals.', 'https://linkedin.com', 'priya@policyradar.in'),
('Anand Kulkarni', 'Legal & Regulatory Lead', 'Fintech Regulatory Sandbox', ARRAY['RBI Sandbox', 'FDI Regulations', 'ESOP Compliance'], 'Specializes in DPIIT compliances, cross-border payments, and fintech compliance sandbox applications.', 'https://linkedin.com', 'anand@policyradar.in');

