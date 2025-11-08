# Railway Deployment Guide for VinVerse Backend

## 🚀 Quick Setup

### 1. Deploy to Railway

1. **Connect your repository** to Railway
2. **Select the backend directory** as the root
3. **Railway will auto-detect** Python and install dependencies

### 2. Required Environment Variables

Set these in Railway Dashboard → Your Service → Variables:

#### **Required - Supabase Database:**
```env
# Option 1: Use connection string (Recommended)
SUPABASE_DB_URL=postgresql://postgres:[YOUR-PASSWORD]@db.pzvqevdqywmbmgpfamcz.supabase.co:5432/postgres

# Option 2: Use individual settings
SUPABASE_DB_HOST=db.pzvqevdqywmbmgpfamcz.supabase.co
SUPABASE_DB_PASSWORD=[YOUR-DATABASE-PASSWORD]
SUPABASE_DB_USER=postgres
SUPABASE_DB_NAME=postgres
SUPABASE_DB_PORT=5432
```

#### **Required - Django Settings:**
```env
SECRET_KEY=your-super-secret-key-here-generate-a-new-one
DEBUG=False
ALLOWED_HOSTS=web-production-725a.up.railway.app,your-railway-domain.up.railway.app
```

#### **Optional - Supabase API (for future use):**
```env
SUPABASE_URL=https://pzvqevdqywmbmgpfamcz.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
```

### 3. Generate Secret Key

Run this command to generate a secure SECRET_KEY:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 4. Railway Auto-Configuration

Railway automatically provides:
- `PORT` - Server port (handled by Procfile)
- `RAILWAY_ENVIRONMENT` - Set to "production"
- `RAILWAY_PUBLIC_DOMAIN` - Your Railway domain
- `RAILWAY_DEPLOYMENT_ID` - Deployment identifier

### 5. Post-Deployment Steps

After deployment, run migrations:
```bash
railway run python manage.py migrate
```

Or use Railway's CLI:
```bash
railway connect
railway run python manage.py migrate
```

### 6. Verify Deployment

1. **Check health**: Visit `https://your-railway-domain.up.railway.app/api/`
2. **Test API**: Try `https://your-railway-domain.up.railway.app/api/tournaments/`
3. **Check logs**: Railway Dashboard → Deployments → View Logs

## 🔧 Configuration Details

### CORS Configuration

The backend automatically allows:
- Your Railway domain
- Netlify production domain: `https://vinverse-esport.netlify.app`
- All Netlify preview deployments (regex pattern)

### Database Connection

- **Database**: Supabase PostgreSQL
- **SSL**: Required (automatically configured)
- **Connection Pooling**: Enabled (max age: 600 seconds)

### Static Files

Static files are served from `/static/` (collected to `staticfiles/` directory).
For production, consider using a CDN or Railway's static file serving.

## 🐛 Troubleshooting

### Issue: "Supabase database credentials are required"

**Solution**: Make sure you've set either:
- `SUPABASE_DB_URL` (connection string), OR
- All of: `SUPABASE_DB_HOST`, `SUPABASE_DB_PASSWORD`, `SUPABASE_DB_USER`, `SUPABASE_DB_NAME`

### Issue: CORS errors from frontend

**Solution**: 
1. Check that your frontend domain is in `CORS_ALLOWED_ORIGINS`
2. Verify `RAILWAY_ENVIRONMENT` is set (Railway sets this automatically)
3. Check Railway logs for CORS errors

### Issue: Database connection fails

**Solution**:
1. Verify Supabase credentials are correct
2. Check that Supabase allows connections from Railway IPs
3. Ensure SSL is enabled (it's automatic in the config)

### Issue: Migrations not applied

**Solution**: Run migrations manually:
```bash
railway run python manage.py migrate
```

## 📝 Environment Variable Checklist

Before deploying, ensure you have:

- [ ] `SUPABASE_DB_URL` or all `SUPABASE_DB_*` variables
- [ ] `SECRET_KEY` (generate a new one for production!)
- [ ] `DEBUG=False`
- [ ] `ALLOWED_HOSTS` includes your Railway domain
- [ ] `SUPABASE_URL` and `SUPABASE_ANON_KEY` (optional, for API features)

## 🔗 Frontend Configuration

Update your frontend `.env` file (or Netlify environment variables):

```env
VITE_API_URL=https://your-railway-domain.up.railway.app/api/
```

Or the frontend will automatically use the Railway URL in production.

## 📊 Monitoring

- **Logs**: Railway Dashboard → Deployments → View Logs
- **Metrics**: Railway Dashboard → Metrics
- **Database**: Check Supabase Dashboard for connection status

## 🚨 Security Notes

1. **Never commit** `.env` files or secrets to Git
2. **Use Railway's** environment variables for all secrets
3. **Generate a new** `SECRET_KEY` for production
4. **Set `DEBUG=False`** in production
5. **Keep Supabase password** secure and never expose it

## ✅ Deployment Checklist

- [ ] Repository connected to Railway
- [ ] All environment variables set
- [ ] `SECRET_KEY` generated and set
- [ ] `DEBUG=False` for production
- [ ] Supabase credentials configured
- [ ] Migrations run successfully
- [ ] API endpoints accessible
- [ ] CORS working with frontend
- [ ] Database connection verified

