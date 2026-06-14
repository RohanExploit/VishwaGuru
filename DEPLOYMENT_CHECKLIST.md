# 🚀 VishwaGuru Deployment Checklist

Use this checklist when deploying VishwaGuru to production.

## Pre-Deployment Setup

### 1. Get API Keys & Tokens

- [ ] **Telegram Bot Token**
  - Go to [@BotFather](https://t.me/botfather)
  - Create bot with `/newbot`
  - Save the token (format: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)

- [ ] **Google Gemini API Key**
  - Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
  - Create API key
  - Save the key (format: `AIzaSyABcDEfGhIjKlMnOpQrStUvWxYz`)

## Deployment Steps

### Step 1: Database (Neon) ⚡

- [ ] Go to https://console.neon.tech/
- [ ] Create account / Sign in with GitHub
- [ ] Click "Create a project"
- [ ] Name: `vishwaguru`
- [ ] Choose region closest to users
- [ ] Copy connection string:
  ```
  postgresql://user:pass@ep-xxx.region.aws.neon.tech/dbname?sslmode=require
  ```
- [ ] Save connection string for next step

**Time**: ~2 minutes

---

### Step 2: Backend (Render) 🔧

- [ ] Go to https://dashboard.render.com/
- [ ] Click "New +" → "Web Service"
- [ ] Connect GitHub repository
- [ ] Configure service:
  - **Name**: `vishwaguru-backend`
  - **Runtime**: `Python 3`
  - **Build Command**: `pip install -r backend/requirements.txt`
  - **Start Command**: `python -m uvicorn backend.main:app --host 0.0.0.0 --port $PORT`

- [ ] Add environment variables:
  - `PYTHON_VERSION` = `3.12.0`
  - `TELEGRAM_BOT_TOKEN` = `your_telegram_token`
  - `GEMINI_API_KEY` = `your_gemini_key`
  - `DATABASE_URL` = `your_neon_connection_string`
  - `FRONTEND_URL` = `*` (update later)

- [ ] Click "Create Web Service"
- [ ] Wait for deployment (~3-5 minutes)
- [ ] Copy backend URL: `https://vishwaguru-backend.onrender.com`
- [ ] Test health endpoint: `https://your-backend/health`
  - Should return: `{"status": "ok"}`

**Time**: ~5-7 minutes

---

### Step 3: Frontend (Netlify) 🌐

- [ ] Go to https://app.netlify.com/
- [ ] Click "Add new site" → "Import an existing project"
- [ ] Connect to GitHub
- [ ] Select repository
- [ ] Netlify should auto-detect settings from `netlify.toml`
- [ ] Verify settings:
  - **Base directory**: `frontend`
  - **Build command**: `npm run build`
  - **Publish directory**: `frontend/dist`

- [ ] Add environment variable:
  - `VITE_API_URL` = `https://your-backend.onrender.com` (from Step 2)

- [ ] Click "Deploy site"
- [ ] Wait for deployment (~2-3 minutes)
- [ ] Copy frontend URL: `https://your-app.netlify.app`

**Time**: ~3-5 minutes

---

### Step 4: Update Backend CORS 🔄

- [ ] Go back to Render dashboard
- [ ] Open your backend service
- [ ] Go to "Environment"
- [ ] Update `FRONTEND_URL`:
  - Change from `*` to `https://your-app.netlify.app` (from Step 3)
- [ ] Save changes (triggers automatic redeploy)
- [ ] Wait for redeploy (~2-3 minutes)

**Time**: ~3 minutes

---

## Post-Deployment Testing

### Backend Tests

- [ ] Visit `https://your-backend.onrender.com/health`
  - ✅ Should return: `{"status": "ok"}`
  
- [ ] Visit `https://your-backend.onrender.com/api/responsibility-map`
  - ✅ Should return JSON data

### Frontend Tests

- [ ] Visit `https://your-app.netlify.app`
  - ✅ Page loads without errors
  
- [ ] Click "Who is Responsible?"
  - ✅ Responsibility map loads
  
- [ ] Click "Start an Issue"
  - ✅ Form displays
  
- [ ] Fill form and submit
  - ✅ Action plan generates
  - ✅ WhatsApp and Email drafts appear

### Telegram Bot Tests

- [ ] Open Telegram
- [ ] Search for your bot username
- [ ] Send `/start`
  - ✅ Bot responds with welcome message
  
- [ ] Send a photo
  - ✅ Bot asks for description
  
- [ ] Send description text
  - ✅ Bot asks for category
  
- [ ] Select category
  - ✅ Bot confirms issue saved with reference ID

### Database Tests

- [ ] Go to Neon console
- [ ] Check your project
- [ ] View "Tables" tab
  - ✅ `issues` table exists
  - ✅ Table has data (from your test submissions)

---

## Troubleshooting

### ❌ Backend won't start
**Check**:
- Is `DATABASE_URL` set correctly?
- Does it include `?sslmode=require`?
- Are all env vars set?

### ❌ CORS errors in browser
**Check**:
- Is `FRONTEND_URL` set to exact Netlify URL?
- No trailing slash in URLs?
- Did backend redeploy after updating `FRONTEND_URL`?

### ❌ API calls fail
**Check**:
- Is `VITE_API_URL` set in Netlify?
- No trailing slash in `VITE_API_URL`?
- Is backend actually running?

### ❌ Telegram bot not responding
**Check**:
- Is `TELEGRAM_BOT_TOKEN` correct?
- Check Render logs for errors
- Test token with @BotFather

---

## Success! 🎉

You've successfully deployed VishwaGuru!

**Your URLs**:
- Frontend: `https://your-app.netlify.app`
- Backend: `https://your-backend.onrender.com`
- Database: Managed by Neon
- Bot: Active on Telegram

**Total Time**: ~15-20 minutes

---

## Optional: Custom Domains

### Frontend (Netlify)
1. Go to Site settings → Domain management
2. Add custom domain
3. Configure DNS records as instructed

### Backend (Render)
1. Go to Service settings → Custom domains
2. Add custom domain
3. Configure DNS records as instructed
4. Update `VITE_API_URL` in Netlify to new domain
5. Update `FRONTEND_URL` in Render to new domain

---

## Monitoring

### Check Logs

**Render Backend**:
- Render Dashboard → Your Service → "Logs"

**Netlify Frontend**:
- Netlify Dashboard → Your Site → "Deploys"

**Neon Database**:
- Neon Console → Your Project → "Monitoring"

---

## Need Help?

Refer to detailed guides:
- [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) - Full deployment guide
- [QUICK_REFERENCE.md](./QUICK_REFERENCE.md) - Quick command reference
- [ARCHITECTURE.md](./ARCHITECTURE.md) - Architecture diagrams (ASCII available, visual diagrams missing)

---

**Last Updated**: December 2024
