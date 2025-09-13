-- Initialize database for asset management system
-- This file is executed when PostgreSQL container starts for the first time

-- Create database if it doesn't exist
SELECT 'CREATE DATABASE asset_management_dev'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'asset_management_dev')\gexec

-- Create test database for running tests
SELECT 'CREATE DATABASE test_asset_management_dev'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'test_asset_management_dev')\gexec