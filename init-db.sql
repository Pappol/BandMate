-- Database initialization script for BandMate production
-- This script runs when the PostgreSQL container starts

-- Create the database if it doesn't exist
-- (This is handled by POSTGRES_DB environment variable)

-- Create extensions that might be useful
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Set timezone
SET timezone = 'UTC';

-- Create a read-only user for analytics/monitoring
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'bandmate_readonly') THEN
        CREATE ROLE bandmate_readonly;
    END IF;
END
$$;

-- Grant connect and usage on schema
GRANT CONNECT ON DATABASE bandmate_prod TO bandmate_readonly;
GRANT USAGE ON SCHEMA public TO bandmate_readonly;

-- Grant select on all tables
GRANT SELECT ON ALL TABLES IN SCHEMA public TO bandmate_readonly;

-- Grant select on future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO bandmate_readonly;

-- Create indexes for better performance (these will be created by SQLAlchemy, but good to have)
-- These are examples - actual indexes will be created by the application

-- Log the initialization
INSERT INTO pg_stat_statements_info (dealloc) VALUES (0) ON CONFLICT DO NOTHING;
