#!/bin/bash

# Script to start PostgreSQL service on macOS
# This script helps start PostgreSQL if it's not running

echo "🔍 Checking PostgreSQL status..."

# Check if PostgreSQL is running
if pg_isready -h localhost -p 5432 &> /dev/null; then
    echo "✅ PostgreSQL is already running!"
    exit 0
fi

echo "⚠️  PostgreSQL is not running. Attempting to start..."

# Try different methods to start PostgreSQL on macOS
if command -v brew &> /dev/null; then
    echo "📦 Using Homebrew to start PostgreSQL..."
    brew services start postgresql@18 || brew services start postgresql || brew services start postgresql@15
elif [ -d "/Library/PostgreSQL/18" ]; then
    echo "📦 Starting PostgreSQL 18..."
    /Library/PostgreSQL/18/bin/pg_ctl -D /Library/PostgreSQL/18/data -l /Library/PostgreSQL/18/data/logfile start
elif [ -d "/usr/local/var/postgres" ]; then
    echo "📦 Starting PostgreSQL from /usr/local/var/postgres..."
    pg_ctl -D /usr/local/var/postgres start
else
    echo "❌ Could not find PostgreSQL installation"
    echo "Please start PostgreSQL manually:"
    echo "  - Homebrew: brew services start postgresql"
    echo "  - Or use: pg_ctl -D <data_directory> start"
    exit 1
fi

# Wait a moment for PostgreSQL to start
sleep 2

# Check if it's running now
if pg_isready -h localhost -p 5432 &> /dev/null; then
    echo "✅ PostgreSQL started successfully!"
else
    echo "❌ Failed to start PostgreSQL"
    echo "Please start it manually and try again"
    exit 1
fi

