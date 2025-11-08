# PostgreSQL Setup Guide for VinVerse

## Phase 1: PostgreSQL Setup

### Prerequisites

1. **Install PostgreSQL**

   - macOS: `brew install postgresql@15` or download from https://www.postgresql.org/download/
   - Linux: `sudo apt-get install postgresql postgresql-contrib` (Ubuntu/Debian)
   - Windows: Download installer from PostgreSQL website

2. **Start PostgreSQL Service**

   ```bash
   # macOS (Homebrew)
   brew services start postgresql@15

   # Linux
   sudo systemctl start postgresql

   # Windows
   # Start from Services or use pg_ctl
   ```

### Quick Setup (Automated)

1. **Run the setup script:**

   ```bash
   cd backend
   ./setup_database.sh
   ```

2. **Or manually create database:**
   ```bash
   createdb vinverse_db
   # Or using psql:
   psql -U postgres -c "CREATE DATABASE vinverse_db;"
   ```

### Manual Setup (Step by Step)

1. **Create database using SQL:**

   ```bash
   psql -U postgres -f setup_database.sql
   ```

2. **Or create database interactively:**

   ```bash
   psql -U postgres
   CREATE DATABASE vinverse_db;
   \q
   ```

3. **Configure environment variables:**

   ```bash
   cd backend
   cp .env.example .env
   # Edit .env file with your database credentials
   ```

4. **Install Python dependencies:**

   ```bash
   source venv/bin/activate
   pip install -r requirements.txt
   ```

5. **Run migrations:**

   ```bash
   python manage.py migrate
   ```

6. **Create superuser (optional):**
   ```bash
   python manage.py createsuperuser
   ```

### Environment Variables

Create a `.env` file in the `backend/` directory:

```env
# Django Settings
SECRET_KEY=your-secret-key-here-change-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration (PostgreSQL)
# Note: On macOS with Homebrew, DB_USER is usually your system username, not "postgres"
DATABASE_ENGINE=postgresql
DB_NAME=vinverse_db
DB_USER=your_username  # Use your system username (run 'whoami' to find it)
DB_PASSWORD=  # Usually empty for local development
DB_HOST=localhost
DB_PORT=5432

# Redis Configuration (Phase 2 - ready to use)
REDIS_URL=redis://127.0.0.1:6379/1
```

### Verify Setup

1. **Test database connection:**

   ```bash
   python manage.py dbshell
   # Should connect to PostgreSQL
   ```

2. **Check migrations:**

   ```bash
   python manage.py showmigrations
   # All should show [X] (applied)
   ```

3. **Start server:**
   ```bash
   python manage.py runserver
   # Should start without database errors
   ```

## Phase 2: Redis Setup (Ready for Integration)

Redis is already configured in `settings.py` and ready to use. To set it up:

1. **Install Redis:**

   ```bash
   # macOS
   brew install redis

   # Linux
   sudo apt-get install redis-server

   # Windows
   # Download from https://redis.io/download
   ```

2. **Start Redis:**

   ```bash
   # macOS
   brew services start redis

   # Linux
   sudo systemctl start redis
   ```

3. **Test Redis connection:**

   ```bash
   redis-cli ping
   # Should return: PONG
   ```

4. **Redis is already configured in settings.py:**
   - Cache backend: `django_redis.cache.RedisCache`
   - Session backend: Uses Redis cache
   - Default location: `redis://127.0.0.1:6379/1`

## Troubleshooting

### PostgreSQL Connection Issues

1. **Check if PostgreSQL is running:**

   ```bash
   pg_isready -h localhost -p 5432
   ```

2. **Check PostgreSQL version:**

   ```bash
   psql --version
   ```

3. **Verify database exists:**

   ```bash
   psql -U postgres -l | grep vinverse_db
   ```

4. **Test connection manually:**
   ```bash
   psql -U postgres -d vinverse_db -c "SELECT version();"
   ```

### Common Issues

- **"FATAL: password authentication failed"**

  - Check `.env` file for correct `DB_PASSWORD`
  - Verify PostgreSQL user password

- **"FATAL: database does not exist"**

  - Run `createdb vinverse_db` or use setup script

- **"Connection refused"**

  - Ensure PostgreSQL service is running
  - Check `DB_HOST` and `DB_PORT` in `.env`

- **"psycopg" module not found**
  - Run `pip install -r requirements.txt`
  - Ensure virtual environment is activated

## Production Considerations

For production deployment:

1. **Use strong SECRET_KEY:**

   ```python
   python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
   ```

2. **Set DEBUG=False:**

   ```env
   DEBUG=False
   ```

3. **Configure proper ALLOWED_HOSTS:**

   ```env
   ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
   ```

4. **Use connection pooling:**

   - Consider using `pgbouncer` for connection pooling
   - Configure `CONN_MAX_AGE` in database settings

5. **Enable SSL for PostgreSQL:**
   ```python
   'OPTIONS': {
       'sslmode': 'require',
   }
   ```
