# Railway Deployment Guide - LeadGen Intelligence Pipeline

## Architecture Overview

This project runs as **two Railway services** connected to a **Supabase** PostgreSQL database:

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Frontend   │────▶│   Backend    │────▶│   Supabase   │
│  (Next.js)   │     │  (FastAPI)   │     │ (PostgreSQL) │
│  Port: 3000  │     │  Port: 8000  │     │   External   │
└──────────────┘     └──────────────┘     └──────────────┘
```

---

## Prerequisites

1. **Railway Account** - [railway.app](https://railway.app)
2. **Supabase Account** - [supabase.com](https://supabase.com)
3. **GitHub Repository** - This repo must be connected to Railway

---

## Step 1: Supabase Database Setup

### 1.1 Create a Supabase Project

1. Go to [supabase.com/dashboard](https://supabase.com/dashboard)
2. Click **"New Project"**
3. Choose a name (e.g., `leadgen-intelligence`)
4. Set a strong database password
5. Choose region closest to your Railway deployment (e.g., `EU West`)

### 1.2 Run the Schema

1. In Supabase Dashboard, go to **SQL Editor**
2. Click **"New Query"**
3. Copy and paste the entire contents of `supabase/schema.sql`
4. Click **"Run"** to execute

### 1.3 Get Your API Keys

1. Go to **Project Settings** → **API**
2. Copy:
   - **Project URL** (e.g., `https://xxxx.supabase.co`)
   - **Service Role Key** (⚠️ secret, for backend only)
   - **Anon/Public Key** (for frontend, if needed)

---

## Step 2: Railway Backend Deployment

### 2.1 Create Backend Service

1. Go to [Railway Dashboard](https://railway.app/dashboard)
2. Click **"New Project"** → **"Deploy from GitHub Repo"**
3. Select this repository
4. Railway will detect the repo. We need to set the **root directory**.

### 2.2 Configure Backend Service

1. **IMPORTANT**: In the service settings, set:
   - **Root Directory**: `backend` ⚠️ **Must be set correctly**
   - **Builder**: Dockerfile (auto-detected)
   - **Dockerfile Path**: Leave empty (uses `backend/Dockerfile`)

2. Add **Environment Variables**:

| Variable | Value | Description |
|----------|-------|-------------|
| `SUPABASE_URL` | `https://xxxx.supabase.co` | Your Supabase project URL |
| `SUPABASE_KEY` | `eyJhbGciOiJI...` | Supabase **service_role** key |
| `CORS_ORIGINS` | `https://your-frontend.railway.app` | Frontend URL (set after frontend deploy) |
| `PORT` | `8000` | Railway injects this automatically |
| `DEBUG` | `false` | Set to `true` for verbose logging |
| `GOOGLE_MAPS_API_KEY` | (optional) | Google Places API key for better scraping |

3. Click **Deploy**

### 2.3 Get Backend URL

After deployment, Railway assigns a URL like:
```
https://leadgen-backend-production-xxxx.up.railway.app
```

Copy this URL - you'll need it for the frontend.

---

## Step 3: Railway Frontend Deployment

### 3.1 Create Frontend Service

1. In the same Railway project, click **"+ New"** → **"Service"** → **"GitHub Repo"**
2. Select the same repository

### 3.2 Configure Frontend Service

1. **IMPORTANT**: In the service settings, configure the build:
   
   **Settings → Build:**
   - **Root Directory**: `frontend` ⚠️ **Critical**
   - **Dockerfile Path**: Leave **EMPTY** or set to `Dockerfile`
   
   > ⚠️ **Common Mistake**: Do NOT set Dockerfile Path to `frontend/Dockerfile`!  
   > Since Root Directory is already `frontend`, the path is relative to that.
   >
   > ```
   > ✅ CORRECT:
   >    Root Directory: frontend
   >    Dockerfile Path: Dockerfile (or empty)
   >    → Railway uses: frontend/Dockerfile
   >
   > ❌ WRONG:
   >    Root Directory: frontend  
   >    Dockerfile Path: frontend/Dockerfile
   >    → Railway looks for: frontend/frontend/Dockerfile (doesn't exist)
   >    → Falls back to: Dockerfile (root - Go scraper!)
   > ```

2. Add **Environment Variables**:

| Variable | Value | Description |
|----------|-------|-------------|
| `BACKEND_URL` | `http://google-maps-scraper.railway.internal:8000` | Backend internal URL (Railway private network) |
| `PORT` | `3000` | Injected automatically |

> **Note:** `BACKEND_URL` is a **runtime** server-side variable (not build-time).
> The frontend uses a server-side API proxy that reads this at runtime.
> No build arguments are needed. Use the Railway **internal URL** for best performance.

3. Click **Deploy**

---

## Step 4: Post-Deployment Configuration

### 4.1 CORS (Optional)

Since the frontend uses a server-side API proxy (all browser requests stay same-origin),
CORS is generally not needed. However, if you want direct API access from other domains,
update `CORS_ORIGINS` in the backend:
```
https://your-frontend-xxxx.up.railway.app
```

### 4.2 Custom Domain (Optional)

1. In Railway, go to your Frontend service
2. Click **Settings** → **Networking** → **Custom Domain**
3. Add your domain (e.g., `leads.yourdomain.com`)
4. Follow DNS instructions

### 4.3 Enable Auto-Deploy

Railway automatically deploys when you push to the `main` branch. To change:
1. Go to Service **Settings** → **Source**
2. Configure branch and deployment triggers

---

## Step 5: Verify Deployment

### Health Check
```bash
curl https://your-backend.up.railway.app/api/health
```

Expected response:
```json
{
  "status": "ok",
  "version": "1.0.0",
  "database": "connected"
}
```

### API Docs
Visit: `https://your-backend.up.railway.app/api/docs`

### Frontend
Visit: `https://your-frontend.up.railway.app`

---

## Environment Variables Reference

### Backend (`backend/`)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SUPABASE_URL` | ✅ | - | Supabase project URL |
| `SUPABASE_KEY` | ✅ | - | Supabase service_role key |
| `PORT` | ❌ | `8000` | Server port (Railway auto-injects) |
| `DEBUG` | ❌ | `false` | Enable debug logging |
| `CORS_ORIGINS` | ❌ | `*` | Comma-separated allowed origins |
| `GOOGLE_MAPS_API_KEY` | ❌ | - | Google Places API key |
| `MAX_CONCURRENT_SCRAPES` | ❌ | `3` | Max parallel scrape jobs |
| `SCRAPE_DELAY_MIN` | ❌ | `2.0` | Min delay between requests (sec) |
| `SCRAPE_DELAY_MAX` | ❌ | `5.0` | Max delay between requests (sec) |

### Frontend (`frontend/`)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `BACKEND_URL` | ✅ | `http://localhost:8000` | Backend API URL (runtime, server-side) |
| `PORT` | ❌ | `3000` | Server port |

> **Architecture:** The frontend uses a server-side API proxy (`/api/[...path]/route.ts`).
> All browser API calls go to the Next.js server, which forwards them to the backend.
> This eliminates CORS issues and allows using Railway internal networking.

---

## Local Development

### Option 1: Docker Compose

```bash
# Create .env files
cp backend/.env.example backend/.env
# Edit backend/.env with your Supabase credentials

# Run both services
docker compose -f docker-compose.leadgen.yaml up --build
```

### Option 2: Run Separately

**Backend:**
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
echo "BACKEND_URL=http://localhost:8000" > .env.local
npm run dev
```

---

## Troubleshooting

### 🎯 Quick Reference: Railway Service Configuration

| Service | Root Directory | Dockerfile Path | First Line of Logs |
|---------|---------------|-----------------|-------------------|
| **Backend** | `backend` | (empty) or `Dockerfile` | `FROM python:3.11-slim` |
| **Frontend** | `frontend` | (empty) or `Dockerfile` | `FROM node:22-alpine AS deps` |

---

### Frontend Build Fails with "go.sum not found" or Go/Playwright Errors

**Problem**: Railway is using the wrong Dockerfile (root `Dockerfile` instead of `frontend/Dockerfile`)

**Root Cause**: One of these common misconfigurations:
1. Root Directory not set to `frontend`
2. Dockerfile Path set to `frontend/Dockerfile` (should be just `Dockerfile` or empty)
3. Railway cached an old configuration

**Solution**:

**Step 1**: Verify configuration in Railway Dashboard:
```
Settings → Build:
  Root Directory: frontend
  Dockerfile Path: (empty) or Dockerfile
```

**Step 2**: If you see `frontend/Dockerfile` in Dockerfile Path:
1. **Change it to**: `Dockerfile` (no path prefix)
2. Or **clear it completely**
3. Click **Save**

**Step 3**: If it still fails:
1. Go to **Deployments** tab
2. Find the latest deployment
3. Click **View Logs**
4. Look for "Using Dockerfile: ..." at the start
5. If it shows the root Dockerfile, the config isn't saved

**Step 4**: Nuclear option (if settings won't save):
1. **Delete the service** completely
2. Create new service:
   - Deploy from GitHub
   - Select repository
   - **Immediately** in Settings → Build:
     - Set Root Directory: `frontend`  
     - Leave Dockerfile Path empty
   - Add environment variables
   - Deploy

**How to verify it's working**: 
The build logs should start with:
```
FROM node:22-alpine AS deps
```

NOT with:
```
FROM ubuntu:20.04 AS playwright-deps
```

### "Database disconnected"
- Check `SUPABASE_URL` and `SUPABASE_KEY` environment variables
- Ensure the SQL schema has been executed in Supabase

### "CORS Error"
- Update `CORS_ORIGINS` in the backend with the frontend URL
- For development, set `CORS_ORIGINS=*`

### Other Build Failures
- Ensure `Root Directory` is set correctly in Railway
- Check Railway build logs for specific errors
- Verify the correct `railway.toml` exists in the service directory

### Scraping Returns Empty
- The scraper uses the Go binary or Google Places API
- For best results, set `GOOGLE_MAPS_API_KEY`
- Demo data from `bucharest-results.json` is used as fallback

---

## Cost Estimation (Railway)

| Service | RAM | CPU | Estimated Cost |
|---------|-----|-----|----------------|
| Backend (FastAPI) | 512MB | 0.5 vCPU | ~$5/month |
| Frontend (Next.js) | 512MB | 0.5 vCPU | ~$5/month |
| **Total** | | | **~$10/month** |

Supabase Free Tier includes:
- 500MB database storage
- 2GB bandwidth
- 50,000 monthly active users
