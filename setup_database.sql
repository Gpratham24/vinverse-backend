-- VinVerse PostgreSQL Database Setup SQL Script
-- Run this script as PostgreSQL superuser (postgres)

-- Create database
CREATE DATABASE vinverse_db;

-- Optional: Create dedicated user (uncomment if needed)
-- CREATE USER vinverse_user WITH PASSWORD 'your_secure_password';
-- GRANT ALL PRIVILEGES ON DATABASE vinverse_db TO vinverse_user;

-- Connect to the database and set up extensions (optional)
-- \c vinverse_db
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Verify database creation
SELECT datname FROM pg_database WHERE datname = 'vinverse_db';

