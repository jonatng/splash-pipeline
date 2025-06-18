-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    supabase_uid VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE,
    preferences JSONB DEFAULT '{}'::jsonb
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_supabase_uid ON users(supabase_uid);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Set up RLS (Row Level Security)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Users can view their own data"
    ON users FOR SELECT
    USING (auth.uid()::text = supabase_uid);

CREATE POLICY "Users can update their own data"
    ON users FOR UPDATE
    USING (auth.uid()::text = supabase_uid);

-- Grant permissions to authenticated users
GRANT SELECT, UPDATE ON users TO authenticated;

-- Comments
COMMENT ON TABLE users IS 'Table storing additional user information for authenticated users';
COMMENT ON COLUMN users.id IS 'Primary key for the users table';
COMMENT ON COLUMN users.email IS 'User email address, must match Supabase auth email';
COMMENT ON COLUMN users.supabase_uid IS 'Supabase auth user ID';
COMMENT ON COLUMN users.full_name IS 'User full name';
COMMENT ON COLUMN users.is_active IS 'Whether the user account is active';
COMMENT ON COLUMN users.is_superuser IS 'Whether the user has admin privileges';
COMMENT ON COLUMN users.created_at IS 'Timestamp when the user record was created';
COMMENT ON COLUMN users.updated_at IS 'Timestamp when the user record was last updated';
COMMENT ON COLUMN users.last_login IS 'Timestamp of the user last login';
COMMENT ON COLUMN users.preferences IS 'JSON object storing user preferences'; 