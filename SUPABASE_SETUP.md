# Supabase Database Setup Guide

## ⚠️ IMPORTANT: Supabase is Now Required

The backend has been configured to **require Supabase** as the database. SQLite fallback has been removed to ensure all data is stored in Supabase.

## Quick Setup

### Step 1: Get Your Supabase Connection String

1. Go to your Supabase project: https://pzvqevdqywmbmgpfamcz.supabase.co
2. Navigate to **Settings** → **Database**
3. Find the **Connection string** section
4. Copy the **URI** connection string (it looks like):
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.pzvqevdqywmbmgpfamcz.supabase.co:5432/postgres
   ```

### Step 2: Configure Environment Variables

Create or update your `.env` file in the `backend/` directory:

**Option 1: Connection String (Recommended)**
```env
SUPABASE_DB_URL=postgresql://postgres:[YOUR-PASSWORD]@db.pzvqevdqywmbmgpfamcz.supabase.co:5432/postgres
```

**Option 2: Individual Settings**
```env
SUPABASE_DB_HOST=db.pzvqevdqywmbmgpfamcz.supabase.co
SUPABASE_DB_PASSWORD=[YOUR-DATABASE-PASSWORD]
SUPABASE_DB_USER=postgres
SUPABASE_DB_NAME=postgres
SUPABASE_DB_PORT=5432
```

### Step 3: Run Migrations

```bash
cd backend
source venv/bin/activate
python manage.py migrate
```

### Step 4: Start the Server

```bash
python manage.py runserver
```

## Verification

The server will show one of these messages when starting:
- ✅ `Using Supabase DATABASE_URL for database connection`
- ✅ `Using DATABASE_URL for Supabase connection`
- ✅ `Using Supabase PostgreSQL with host: [hostname]`

If you see an error about missing Supabase credentials, check your `.env` file.

## Troubleshooting

### Error: "Supabase database credentials are required"

**Solution:** Make sure your `.env` file contains either:
- `SUPABASE_DB_URL` (connection string), OR
- All of: `SUPABASE_DB_HOST`, `SUPABASE_DB_PASSWORD`, `SUPABASE_DB_USER`, `SUPABASE_DB_NAME`

### Error: "connection refused" or "SSL required"

**Solution:** 
- Verify your Supabase password is correct
- Ensure SSL is enabled (it's automatically set to `require` in the config)
- Check that your Supabase project is active

### Error: "database does not exist"

**Solution:** 
- The database name should be `postgres` (default Supabase database)
- If using a custom database, update `SUPABASE_DB_NAME` in your `.env`

## Notes

- The backend will **NOT** fall back to SQLite anymore
- All database operations will use Supabase PostgreSQL
- SSL is automatically required for all connections
- Connection pooling is enabled (max age: 600 seconds)

