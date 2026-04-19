ALTER TABLE schemes_clean ADD COLUMN IF NOT EXISTS application_status TEXT DEFAULT 'Unknown';
ALTER TABLE schemes_clean ADD COLUMN IF NOT EXISTS next_deadline TIMESTAMPTZ;
ALTER TABLE schemes_clean ADD COLUMN IF NOT EXISTS last_source_updated_at TIMESTAMPTZ;
ALTER TABLE schemes_clean ADD COLUMN IF NOT EXISTS equity_or_grant TEXT;
ALTER TABLE schemes_clean ADD COLUMN IF NOT EXISTS disbursement_structure TEXT;

CREATE TABLE IF NOT EXISTS user_applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_email TEXT NOT NULL,
    scheme_id UUID NOT NULL REFERENCES schemes_clean(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'interested',
    applied_at TIMESTAMPTZ,
    next_action TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
