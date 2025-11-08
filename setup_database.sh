#!/bin/bash

# VinVerse PostgreSQL Database Setup Script
# This script creates the database and user for VinVerse

echo "🚀 Setting up PostgreSQL database for VinVerse..."

# Database configuration (can be overridden by environment variables)
DB_NAME="${DB_NAME:-vinverse_db}"
DB_USER="${DB_USER:-postgres}"
DB_PASSWORD="${DB_PASSWORD:-postgres}"

# Check if PostgreSQL is running
if ! command -v psql &> /dev/null; then
    echo "❌ PostgreSQL is not installed or not in PATH"
    echo "Please install PostgreSQL first: https://www.postgresql.org/download/"
    exit 1
fi

# Check if PostgreSQL service is running
if ! pg_isready -h localhost -p 5432 &> /dev/null; then
    echo "❌ PostgreSQL service is not running"
    echo "Please start PostgreSQL service first"
    exit 1
fi

echo "✅ PostgreSQL is running"

# Create database
echo "📦 Creating database: $DB_NAME..."
psql -U postgres -c "CREATE DATABASE $DB_NAME;" 2>/dev/null || echo "Database $DB_NAME already exists or creation failed"

# Create user if it doesn't exist (optional - using postgres user by default)
# Uncomment below if you want to create a dedicated user
# echo "👤 Creating user: $DB_USER..."
# psql -U postgres -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';" 2>/dev/null || echo "User $DB_USER already exists"
# psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;" 2>/dev/null || echo "Grant failed"

echo "✅ Database setup complete!"
echo ""
echo "📝 Next steps:"
echo "1. Copy .env.example to .env and update database credentials if needed"
echo "2. Run: python manage.py migrate"
echo "3. Run: python manage.py createsuperuser (optional)"
echo "4. Start server: python manage.py runserver"

