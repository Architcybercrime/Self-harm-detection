# 🚀 Deployment Guide for SafeSignal

This guide provides production deployment instructions for Render, Vercel, and other platforms.

## 📋 Prerequisites

- Python 3.10+ installed locally
- Git repository initialized
- GitHub account with the project repository
- Supabase account (for production database)

---

## 🔧 Environment Setup

### 1. Create Production `.env` File

Copy `.env.example` and create `.env` with production values:

```bash
cp .env.example .env
```

**Critical Variables:**
```
ENVIRONMENT=production
JWT_SECRET_KEY=<generate-with: python -c "import secrets; print(secrets.token_urlsafe(32))">
SUPABASE_URL=<your-supabase-url>
SUPABASE_KEY=<your-supabase-api-key>
MAX_UPLOAD_SIZE=500
LOG_LEVEL=INFO
```

**DO NOT commit `.env` to Git. Add to `.gitignore`:**
```
.env
.env.local
.env.*.local
```

---

## ☁️ Deployment on Render

### Step 1: Create Render Account
1. Go to [render.com](https://render.com)
2. Sign up with GitHub account
3. Connect your GitHub repository

### Step 2: Configure Backend Service
1. Click "New +" → "Web Service"
2. Select your repository
3. **Name:** `safesignal-backend`
4. **Runtime:** Python 3.11
5. **Build Command:**
```bash
pip install --upgrade pip setuptools wheel && pip install -r backend/requirements.txt
```
6. **Start Command:**
```bash
gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT --timeout 300 --access-logfile - --error-logfile - backend.wsgi:app
```

### Step 3: Set Environment Variables (Render Dashboard)
1. Go to "Environment"
2. Add these variables:
   - `JWT_SECRET_KEY` (generate new value)
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `ENVIRONMENT=production`
   - `MAX_UPLOAD_SIZE=500`
   - `LOG_LEVEL=INFO`

### Step 4: Configure Frontend (Static Site)
1. Click "New +" → "Static Site"
2. Select your repository
3. **Name:** `safesignal-frontend`
4. **Build Command:** Leave empty (use default)
5. **Publish Directory:** `frontend`

### Step 5: Update CORS in Frontend
Update frontend files to use Render URLs:
- Backend URL: `https://safesignal-backend.onrender.com`
- Frontend URL: `https://safesignal-frontend.onrender.com`

---

## 🌐 Deployment on Vercel (Frontend Only)

### Step 1: Deploy Frontend
```bash
npm install -g vercel
vercel --prod
```

### Step 2: Configure Environment
Vercel Project Settings → Environment Variables:
```
VITE_API_BASE_URL=https://safesignal-backend.onrender.com/api
```

### Step 3: Update Backend CORS
In `backend/app.py`, add Vercel frontend URL to `ALLOWED_ORIGINS`:
```python
ALLOWED_ORIGINS = [
    ...existing URLs...,
    "https://your-app.vercel.app",
]
```

---

## ✅ Pre-Deployment Checklist

- [ ] All tests pass: `pytest -q`
- [ ] No hardcoded secrets in code
- [ ] `.env` file in `.gitignore`
- [ ] Requirements.txt updated with all dependencies
- [ ] Procfile syntax correct
- [ ] CORS origins configured for production domains
- [ ] JWT_SECRET_KEY set to secure 32+ character string
- [ ] Database credentials (Supabase) in environment variables
- [ ] File upload size limits configured (MAX_UPLOAD_SIZE)
- [ ] Logging configured to stdout (not files)

---

## 📊 Monitoring & Logging

### View Logs on Render
1. Dashboard → Backend Service → "Logs" tab
2. Real-time monitoring of errors and requests

### Key Log Messages to Monitor
```
[INFO] ML models loaded
[WARNING] JWT_SECRET_KEY not set - using insecure development default
[ERROR] Video upload error: ...
[ERROR] Facial analysis error: ...
[ERROR] Text prediction error: ...
```

### Configure Log Level
Set `LOG_LEVEL` env var to:
- `DEBUG`: Verbose, development only
- `INFO`: Normal operation
- `WARNING`: Potential issues
- `ERROR`: Errors only

---

## 🔒 Security Best Practices

1. **JWT Secret:** Minimum 32 characters, rotate periodically
2. **CORS Origins:** Only allow production domains
3. **Rate Limiting:** Enabled on all endpoints (backend/app.py)
4. **File Uploads:** Max 500MB, validated file types only
5. **Input Sanitization:** All user inputs sanitized before processing
6. **HTTPS:** Always use in production (Render handles this)
7. **Database:** Use Supabase SSL connections only

---

## 🚨 Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'app'"
**Solution:** Ensure working directory is `backend/` when running commands

### Issue: "JWT token expired" on every request
**Solution:** Check JWT_SECRET_KEY consistency between services

### Issue: Video upload returns 500 error
**Solution:** Check logs for moviepy errors; verify temp directory exists

### Issue: CORS errors in browser console
**Solution:** Add frontend domain to ALLOWED_ORIGINS in backend/app.py

### Issue: "413 Request Entity Too Large"
**Solution:** Increase MAX_UPLOAD_SIZE in environment variables

---

## 📈 Performance Tuning

### Render Settings
- **Dyno Type:** Standard (2 vCPU, 1GB RAM) minimum
- **Auto-Scaling:** Enable for traffic spikes
- **Worker Processes:** 1 (Gunicorn with eventlet for SocketIO)
- **Request Timeout:** 300 seconds (for long video processing)

### Optimize Cold Starts
- Pre-compile Python files locally
- Use Python 3.11+ for better performance
- Minimize dependencies in requirements.txt

---

## 🔄 Continuous Deployment

### GitHub Actions (Auto-deploy on push)
Create `.github/workflows/deploy.yml`:
```yaml
name: Deploy to Render

on:
  push:
    branches: [main, production]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Tests
        run: |
          pip install -r backend/requirements.txt
          pytest backend/tests -q
      - name: Deploy to Render
        run: |
          curl -X POST ${{ secrets.RENDER_DEPLOY_URL }}
```

---

## 📞 Support & Resources

- **Render Docs:** https://render.com/docs
- **Vercel Docs:** https://vercel.com/docs
- **Flask Deployment:** https://flask.palletsprojects.com/en/latest/deploying/
- **Gunicorn:** https://gunicorn.org/
- **JWT Security:** https://tools.ietf.org/html/rfc7519

---

**Last Updated:** 2026-04-30  
**Version:** 1.0.0
