# Quick Deployment Reference

## ✅ Correct Configuration

### Database (Neon) - Setup First!
```bash
1. Create project at https://console.neon.tech/
2. Copy connection string (includes ?sslmode=require)
3. Use this string in Render's DATABASE_URL
```

### Backend (Render)
```bash
Build Command: pip install -r backend/requirements.txt
Start Command: python -m uvicorn backend.main:app --host 0.0.0.0 --port $PORT

Environment Variables:
- TELEGRAM_BOT_TOKEN (from @BotFather)
- GEMINI_API_KEY (from Google AI Studio)
- FRONTEND_URL (your Netlify URL)
- DATABASE_URL (your Neon connection string)
```

### Frontend (Netlify)
```bash
Base directory: frontend
Build command: npm run build
Publish directory: frontend/dist

Environment Variables:
- VITE_API_URL (your Render backend URL)
```

## ❌ Common Mistakes

### Database
- ❌ Creating PostgreSQL in Render (use Neon instead!)
- ❌ Forgetting ?sslmode=require in connection string
- ❌ Not copying the full Neon connection string

### Backend
- ❌ `python -m bot` - Only starts bot, not web server
- ❌ `./render-build.sh` - Builds frontend unnecessarily
- ❌ Not setting DATABASE_URL to Neon connection string
- ❌ Not setting FRONTEND_URL after deploying frontend

### Frontend  
- ❌ Wrong base directory (should be `frontend/`)
- ❌ Forgetting VITE_API_URL environment variable
- ❌ Adding trailing slash to API URL

## 🔗 URLs After Deployment

- Database: `ep-xxx.region.aws.neon.tech` (from Neon)
- Backend: `https://vishwaguru-backend.onrender.com`
- Frontend: `https://your-app.netlify.app`
- Health Check: `https://your-backend/health`

## 📝 Deployment Order

1. **First**: Create database on Neon, copy connection string
2. **Second**: Deploy Backend on Render with Neon DATABASE_URL
3. **Third**: Note backend URL
4. **Fourth**: Deploy Frontend on Netlify with backend URL
5. **Fifth**: Update backend FRONTEND_URL with Netlify URL

## 🧪 Testing Checklist

- [ ] Neon database is active and accessible
- [ ] Backend health endpoint returns `{"status": "ok"}`
- [ ] Frontend loads without errors
- [ ] "Who is Responsible?" button works (tests GET)
- [ ] "Start an Issue" form submission works (tests POST)
- [ ] No CORS errors in browser console
- [ ] Telegram bot responds to /start command
- [ ] Database tables are created automatically

## 🆘 Quick Fixes

**CORS Error?**
→ Update FRONTEND_URL in Render to match Netlify URL exactly

**API not found?**
→ Check VITE_API_URL in Netlify (no trailing slash)

**Backend not starting?**
→ Verify DATABASE_URL is set to Neon connection string with ?sslmode=require

**Database connection error?**
→ Check Neon connection string is correct and includes ?sslmode=require

**Frontend build failed?**
→ Check base directory is set to `frontend/`

**Neon database suspended?**
→ It will auto-wake on connection (free tier behavior)
