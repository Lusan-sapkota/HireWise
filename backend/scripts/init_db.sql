-- =============================================================================
-- HireWise Database Initialization Script
-- =============================================================================

-- Create database if it doesn't exist (for PostgreSQL)
-- This script runs when the PostgreSQL container starts

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "unaccent";

-- Create indexes for better performance (will be created after Django migrations)
-- These are commented out as they will be created by Django migrations
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jobpost_title_trgm ON matcher_jobpost USING gin (title gin_trgm_ops);
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jobpost_description_trgm ON matcher_jobpost USING gin (description gin_trgm_ops);
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jobpost_skills_trgm ON matcher_jobpost USING gin (skills_required gin_trgm_ops);

-- Set default timezone
SET timezone = 'UTC';

-- Create a function for updating timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON DATABASE hirewise_db TO hirewise_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO hirewise_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO hirewise_user;

-- Set default permissions for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO hirewise_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO hirewise_user;