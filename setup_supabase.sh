#!/bin/bash

# Helper script to set Supabase password in .env file

echo "🔧 Supabase Database Setup"
echo "=========================="
echo ""
echo "This script will help you configure Supabase in your .env file."
echo ""
read -sp "Enter your Supabase database password: " SUPABASE_PASSWORD
echo ""

if [ -z "$SUPABASE_PASSWORD" ]; then
    echo "❌ Error: Password cannot be empty"
    exit 1
fi

# Update .env file
cd "$(dirname "$0")"

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found"
    exit 1
fi

# Update SUPABASE_DB_PASSWORD
if grep -q "^SUPABASE_DB_PASSWORD=" .env; then
    # Use sed to update the password (works on macOS)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s|^SUPABASE_DB_PASSWORD=.*|SUPABASE_DB_PASSWORD=$SUPABASE_PASSWORD|" .env
    else
        sed -i "s|^SUPABASE_DB_PASSWORD=.*|SUPABASE_DB_PASSWORD=$SUPABASE_PASSWORD|" .env
    fi
    echo "✅ Updated SUPABASE_DB_PASSWORD in .env file"
else
    echo "❌ Error: SUPABASE_DB_PASSWORD not found in .env file"
    exit 1
fi

echo ""
echo "✅ Configuration complete!"
echo ""
echo "Next steps:"
echo "1. Run: python manage.py migrate"
echo "2. Run: python manage.py runserver"
echo ""

