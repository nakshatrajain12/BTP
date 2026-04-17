CREATE TABLE IF NOT EXISTS scheme_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scheme_id UUID REFERENCES schemes_clean(id) ON DELETE CASCADE,
    scheme_name TEXT,
    ministry TEXT,
    changed_at TIMESTAMPTZ DEFAULT NOW(),
    changed_fields TEXT[],
    old_values JSONB,
    new_values JSONB
);
