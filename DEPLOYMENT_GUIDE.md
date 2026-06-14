# Deployment Guide: Netlify (Frontend) + Render (Backend) + Neon (Database)

This guide explains how to deploy VishwaGuru with the frontend on Netlify, backend on Render, and database on Neon.

## Architecture Overview

```
┌─────────────────┐         API Requests        ┌─────────────────┐
│   Netlify       │  ────────────────────────>  │   Render        │
│   (Frontend)    │                              │   (Backend)     │
│   React + Vite  │  <────────────────────────  │   FastAPI       │
└─────────────────┘         API Responses       └─────────────────┘
                                                          │
                                                          │
                                                          ▼
                                                 ┌─────────────────┐
                                                 │   Neon          │
                                                 │   PostgreSQL    │
                                                 │   (Serverless)  │
                                                 └─────────────────┘
```

## Part 0: Setup Neon Database (Do This First!)

### Step 1: Create Neon Account

1. Go to [Neon Console](https://console.neon.tech/)
2. Sign up or log in with GitHub
3. Click "Create a project"

### Step 2: Configure Database

1. **Project Name**: `vishwaguru` (or any name you prefer)
2. **Region**: Choose closest to your users (e.g., US East, EU West, Asia Pacific)
3. **PostgreSQL Version**: 16 (or latest stable)
4. Click "Create Project"

### Step 3: Get Connection String

1. After project creation, you'll see the connection details
2. Copy the **Connection string** - it looks like:
   ```
   postgresql://username:password@ep-xxx-xxx.region.aws.neon.tech/dbname?sslmode=require
   ```
3. Save this connection string - you'll need it for the Render backend

**Important Notes**:
- Neon provides a **serverless PostgreSQL** database
- Free tier includes: 0.5 GB storage, 1 compute unit
- Database auto-scales and auto-suspends when not in use
- Connection pooling is built-in

## Part 1: Deploy Backend on Render

### Step 1: Create a Web Service on Render

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure the service:

### Step 2: Configure Build Settings

**Service Name**: `vishwaguru-backend` (or any name you prefer)

**Root Directory**: Leave empty (root of repo)

**Runtime**: `Python 3`

**Build Command**:
```bash
pip install -r backend/requirements.txt
```

**Start Command**:
```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

### Step 3: Set Environment Variables

Add these environment variables in the Render dashboard:

| Key | Value | Notes |
|-----|-------|-------|
| `PYTHON_VERSION` | `3.12.0` | Python version |
| `TELEGRAM_BOT_TOKEN` | `your_bot_token` | Get from @BotFather on Telegram |
| `GEMINI_API_KEY` | `your_api_key` | Get from Google AI Studio |
| `FRONTEND_URL` | `https://your-app.netlify.app` | **Add AFTER deploying frontend** |
| `DATABASE_URL` | `postgresql://user:pass@host/db?sslmode=require` | **Your Neon connection string from Part 0** |

**Important**: 
- Copy the exact Neon connection string (includes `?sslmode=require` at the end)
- Leave `FRONTEND_URL` as `*` initially, then update it after deploying the frontend
- The app automatically converts `postgres://` to `postgresql://` if needed

### Step 4: Deploy

1. Click "Create Web Service"
2. Wait for deployment to complete
3. Note your backend URL: `https://vishwaguru-backend.onrender.com` (or similar)
4. Test the health endpoint: `https://your-backend-url.onrender.com/health`

**Note**: You do NOT need to create a PostgreSQL database in Render since you're using Neon.

## Part 2: Deploy Frontend on Netlify

### Step 1: Create Site on Netlify

1. Go to [Netlify Dashboard](https://app.netlify.com/)
2. Click "Add new site" → "Import an existing project"
3. Connect to GitHub and select your repository

### Step 2: Configure Build Settings

Netlify should auto-detect the `netlify.toml` configuration, but verify:

**Base directory**: `frontend`

**Build command**: `npm run build`

**Publish directory**: `frontend/dist`

### Step 3: Set Environment Variables

1. Go to "Site configuration" → "Environment variables"
2. Add the following variable:

| Key | Value | Notes |
|-----|-------|-------|
| `VITE_API_URL` | `https://your-backend.onrender.com` | Your Render backend URL (without trailing slash) |

**Example**: `VITE_API_URL=https://vishwaguru-backend.onrender.com`

### Step 4: Deploy

1. Click "Deploy site"
2. Wait for deployment to complete
3. Note your frontend URL: `https://your-app.netlify.app` (or custom domain)

### Step 5: Update Backend CORS

Now that you have the Netlify URL, go back to Render:

1. Open your backend service settings
2. Go to "Environment" variables
3. Update `FRONTEND_URL` from `*` to your Netlify URL
4. Example: `https://your-app.netlify.app`
5. Save changes (this will trigger a redeploy)

## Testing the Deployment

### 1. Test Backend API

Visit your backend health endpoint:
```
https://your-backend.onrender.com/health
```

Should return:
```json
{"status": "ok"}
```

### 2. Test Frontend

Visit your Netlify URL:
```
https://your-app.netlify.app
```

You should see the VishwaGuru homepage.

### 3. Test Integration

1. Click "Who is Responsible?" button
2. Check if the responsibility map loads (tests GET API)
3. Click "Start an Issue" 
4. Fill out the form and submit (tests POST API)
5. Verify action plan is generated

## Environment Variables Summary

### Backend (Render)

```bash
PYTHON_VERSION=3.12.0
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
GEMINI_API_KEY=AIzaSyABcDEfGhIjKlMnOpQrStUvWxYz
FRONTEND_URL=https://your-app.netlify.app
DATABASE_URL=postgresql://username:password@ep-xxx.region.aws.neon.tech/dbname?sslmode=require
PORT=10000 (auto-set by Render)
```

### Frontend (Netlify)

```bash
VITE_API_URL=https://your-backend.onrender.com
```

### Database (Neon)

No environment variables needed - just copy the connection string from Neon console to Render's `DATABASE_URL`.

## Continuous Deployment

Both Netlify and Render support automatic deployments:

- **Push to `main` branch**: Both services will automatically deploy
- **Pull Request previews**: Netlify creates preview URLs for PRs
- **Rollbacks**: Both services allow rolling back to previous deployments

## Troubleshooting

### CORS Errors

**Problem**: Browser shows CORS errors when frontend tries to call backend

**Solution**:
1. Verify `FRONTEND_URL` is set correctly in Render (must match Netlify URL exactly)
2. Make sure there's no trailing slash in either URL
3. Check browser console for the exact error
4. Redeploy backend after changing `FRONTEND_URL`

### API Calls Failing

**Problem**: Frontend shows "Failed to fetch data" errors

**Solution**:
1. Check `VITE_API_URL` in Netlify is correct
2. Test backend health endpoint directly
3. Open browser DevTools → Network tab to see the actual API requests
4. Verify backend is running (check Render logs)

### Backend Not Starting

**Problem**: Render shows build succeeded but service won't start

**Solution**:
1. Check Render logs for error messages
2. Verify all environment variables are set
3. Test the start command locally: `cd backend && python __main__.py`
4. Check that PostgreSQL database is linked

### Telegram Bot Not Responding

**Problem**: Telegram bot doesn't respond to messages

**Solution**:
1. Verify `TELEGRAM_BOT_TOKEN` is correct
2. Check Render logs for bot-specific errors
3. Test token with @BotFather
4. The bot runs automatically with the FastAPI app

### Build Failures on Netlify

**Problem**: Frontend build fails

**Solution**:
1. Check if `VITE_API_URL` is set
2. Verify Node.js version is compatible (18+)
3. Check Netlify build logs for specific errors
4. Test build locally: `cd frontend && npm run build`

### Database Connection Errors

**Problem**: Backend can't connect to PostgreSQL

**Solution**:
1. Verify Neon connection string is correctly copied to Render's `DATABASE_URL`
2. Ensure connection string includes `?sslmode=require` at the end
3. Check that Neon database is active (doesn't show "suspended")
4. The app automatically converts `postgres://` to `postgresql://`
5. Verify your IP isn't blocked in Neon (Neon allows all IPs by default)
6. Check Render logs for specific connection errors

**Neon-specific notes**:
- Neon databases auto-suspend after inactivity - first connection may be slow
- Connection pooling is built into Neon
- Free tier has 0.5 GB storage limit

## Local Development with Deployed Services

You can develop locally while using deployed services:

### Option 1: Local frontend + Deployed backend

```bash
# In frontend directory
echo "VITE_API_URL=https://your-backend.onrender.com" > .env.local
npm run dev
```

### Option 2: Local backend + Deployed frontend

Update your Render `FRONTEND_URL` to include `http://localhost:5173`:
```bash
FRONTEND_URL=http://localhost:5173,https://your-app.netlify.app
```

Then run locally:
```bash
cd backend
export TELEGRAM_BOT_TOKEN="your_token"
export GEMINI_API_KEY="your_key"
python __main__.py
```

## Monitoring and Logs

### Backend (Render)
- View logs: Render Dashboard → Your Service → "Logs"
- Metrics: Render Dashboard → Your Service → "Metrics"
- Health checks: Automatic via `/health` endpoint

### Frontend (Netlify)
- Deploy logs: Netlify Dashboard → Your Site → "Deploys"
- Function logs: Not applicable (static site)
- Analytics: Netlify Dashboard → Your Site → "Analytics"

## Cost Considerations

### Free Tier Limits

**Render** (Backend):
- 750 hours/month of compute time (Free plan)
- Sleeps after 15 minutes of inactivity
- 100 GB bandwidth/month
- Automatic SSL

**Netlify** (Frontend):
- 100 GB bandwidth/month
- 300 build minutes/month
- Unlimited sites
- Automatic SSL

**Neon** (Database):
- 0.5 GB storage (Free tier)
- 1 compute unit
- Auto-suspend after inactivity (wakes instantly on connection)
- Unlimited databases in free tier
- Connection pooling included
- No time limits (unlike Render's PostgreSQL free tier)

### Optimizations

- Backend may sleep on Render free tier (first request after inactivity will be slow ~30s)
- Neon database auto-suspends and wakes instantly on connection
- Consider upgrading to paid tiers for production use:
  - Render: $7/month (no sleep, always-on)
  - Neon: $19/month (increased storage & compute)
- Use custom domains for better branding

## Security Best Practices

1. **Never commit secrets**: Don't put tokens in code
2. **Use environment variables**: For all sensitive data
3. **Enable HTTPS**: Both Netlify and Render provide free SSL
4. **Set specific CORS origin**: Update `FRONTEND_URL` to exact Netlify URL
5. **Rotate tokens**: Regularly update API keys and bot tokens
6. **Monitor logs**: Check for suspicious activity

## Next Steps

- Set up custom domains for both frontend and backend
- Configure monitoring and alerts
- Set up database backups on Render
- Add performance monitoring (e.g., Sentry)
- Set up CI/CD with GitHub Actions for additional testing

## Support

- **Render Docs**: https://render.com/docs
- **Netlify Docs**: https://docs.netlify.com/
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **Vite Docs**: https://vitejs.dev/
