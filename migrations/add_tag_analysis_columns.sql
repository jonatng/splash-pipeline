-- Add missing columns to tag_analysis table
-- Migration: add_tag_analysis_columns.sql
-- Date: 2024-12-20

-- Add the missing columns
ALTER TABLE tag_analysis 
ADD COLUMN IF NOT EXISTS trend_score FLOAT,
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS co_occurring_tags JSONB;

-- Create index on updated_at for performance
CREATE INDEX IF NOT EXISTS idx_tag_analysis_updated_at ON tag_analysis(updated_at);

-- Create index on trend_score for performance (useful for sorting)
CREATE INDEX IF NOT EXISTS idx_tag_analysis_trend_score ON tag_analysis(trend_score);

-- Create trigger to automatically update updated_at column
CREATE OR REPLACE FUNCTION update_tag_analysis_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER trigger_tag_analysis_updated_at
    BEFORE UPDATE ON tag_analysis
    FOR EACH ROW
    EXECUTE FUNCTION update_tag_analysis_updated_at();

-- Update existing records to set updated_at to current timestamp
UPDATE tag_analysis 
SET updated_at = CURRENT_TIMESTAMP 
WHERE updated_at IS NULL;

-- Add comments for documentation
COMMENT ON COLUMN tag_analysis.trend_score IS 'Calculated trend score for the tag (float value)';
COMMENT ON COLUMN tag_analysis.updated_at IS 'Timestamp when the tag analysis record was last updated';
COMMENT ON COLUMN tag_analysis.co_occurring_tags IS 'JSON array of tags that frequently co-occur with this tag';

-- Grant necessary permissions (adjust as needed for your setup)
GRANT SELECT, INSERT, UPDATE ON tag_analysis TO authenticated; 