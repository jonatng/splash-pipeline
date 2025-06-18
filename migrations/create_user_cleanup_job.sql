-- Function to clean up duplicate users
CREATE OR REPLACE FUNCTION cleanup_duplicate_users()
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER -- Run with elevated privileges
AS $$
DECLARE
    duplicate_record RECORD;
BEGIN
    -- Find duplicate users (keeping the most recently updated record)
    FOR duplicate_record IN (
        SELECT 
            email,
            array_agg(id ORDER BY updated_at DESC) as user_ids,
            array_agg(supabase_uid ORDER BY updated_at DESC) as supabase_uids
        FROM users
        GROUP BY email
        HAVING COUNT(*) > 1
    )
    LOOP
        -- Keep the first record (most recent) and delete others
        DELETE FROM users 
        WHERE email = duplicate_record.email 
        AND id = ANY(duplicate_record.user_ids[2:]);

        -- Log the cleanup
        INSERT INTO cleanup_logs (
            operation,
            details,
            affected_records
        ) VALUES (
            'duplicate_user_cleanup',
            format(
                'Cleaned up duplicate users for email %s. Kept ID: %s, Removed IDs: %s',
                duplicate_record.email,
                duplicate_record.user_ids[1],
                array_to_string(duplicate_record.user_ids[2:], ', ')
            ),
            array_length(duplicate_record.user_ids, 1) - 1
        );
    END LOOP;
END;
$$;

-- Create cleanup logs table to track operations
CREATE TABLE IF NOT EXISTS cleanup_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    operation VARCHAR(255) NOT NULL,
    details TEXT,
    affected_records INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create index on cleanup_logs
CREATE INDEX IF NOT EXISTS idx_cleanup_logs_operation ON cleanup_logs(operation);
CREATE INDEX IF NOT EXISTS idx_cleanup_logs_created_at ON cleanup_logs(created_at);

-- Grant necessary permissions
GRANT EXECUTE ON FUNCTION cleanup_duplicate_users() TO postgres;
GRANT SELECT, INSERT ON cleanup_logs TO postgres;

-- Create cron job to run cleanup every day at 3 AM UTC
SELECT cron.schedule(
    'cleanup-duplicate-users',  -- job name
    '0 3 * * *',              -- cron schedule (every day at 3 AM UTC)
    'SELECT cleanup_duplicate_users();'
);

-- Comments
COMMENT ON FUNCTION cleanup_duplicate_users() IS 'Function to clean up duplicate user records, keeping the most recently updated record';
COMMENT ON TABLE cleanup_logs IS 'Table to track cleanup operations and their results';

-- Create a view to monitor cleanup operations
CREATE OR REPLACE VIEW cleanup_operations_summary AS
SELECT 
    operation,
    COUNT(*) as total_runs,
    SUM(affected_records) as total_records_affected,
    MIN(created_at) as first_run,
    MAX(created_at) as last_run
FROM cleanup_logs
GROUP BY operation;

-- Grant access to the view
GRANT SELECT ON cleanup_operations_summary TO authenticated; 