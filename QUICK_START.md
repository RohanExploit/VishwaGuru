# ⚡ VishwaGuru Quick Start Guide

Get VishwaGuru running in 5 minutes!

---

## 📋 Prerequisites

```bash
✓ Python 3.10+
✓ Node.js 18+
✓ Git
✓ 2GB free disk space
```

---

## 1️⃣ Clone & Setup (1 minute)

```bash
git clone https://github.com/RohanExploit/VishwaGuru.git
cd VishwaGuru

# Backend setup
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r backend/requirements.txt

# Frontend setup
cd frontend && npm install && cd ..
```

---

## 2️⃣ Configure Environment (1 minute)

```bash
cp .env.example .env

# Edit .env and add:
TELEGRAM_BOT_TOKEN=your_token_here
GEMINI_API_KEY=your_key_here
DATABASE_URL=sqlite:///./data/issues.db
FRONTEND_URL=http://localhost:5173
```

---

## 3️⃣ Start Services (2 minutes)

### Terminal 1 - Backend
```bash
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
# Visit: http://127.0.0.1:8000/docs for API docs
# Health check: http://127.0.0.1:8000/health
```

### Terminal 2 - Frontend
```bash
cd frontend
npm run dev
# Visit: http://localhost:5173
```

---

## 4️⃣ Test the App (1 minute)

1. Open http://localhost:5173 in browser
2. Sign up as a user
3. Try uploading an image for issue detection
4. Check http://127.0.0.1:8000/docs for API testing

---

## 🎯 First Steps

### Create an Issue
```bash
curl -X POST "http://127.0.0.1:8000/api/issues" \
  -F "description=Pothole on Main Street" \
  -F "category=pothole" \
  -F "latitude=19.076" \
  -F "longitude=72.877" \
  -F "file=@image.jpg"
```

### List Issues
```bash
curl "http://127.0.0.1:8000/api/issues?skip=0&limit=10"
```

### Detect Issue Type
```bash
curl -X POST "http://127.0.0.1:8000/api/detect-pothole" \
  -F "image=@pothole.jpg"
```

---

## 📊 Architecture at a Glance

```
┌─────────────┐         ┌──────────────┐
│   Frontend  │◄───────►│   Backend    │
│  (React)    │  HTTP   │  (FastAPI)   │
└─────────────┘         └──────────────┘
                                │
                    ┌───────────┼───────────┐
                    ▼           ▼           ▼
                  SQLite      Gemini    HuggingFace
                (local)       (text)    (images)
```

---

## 🔧 Common Commands

```bash
# Run backend tests
pytest backend/tests/ -v

# Build frontend
npm run build

# Database migration
python backend/init_db.py

# API documentation
open http://127.0.0.1:8000/docs

# Check database
sqlite3 data/issues.db ".tables"

# Stop services
Ctrl+C on both terminals
```

---

## 📁 Project Structure

```
VishwaGuru/
├── backend/                # FastAPI application
│   ├── main.py            # Entry point
│   ├── routers/           # API endpoints
│   ├── models.py          # Database models
│   ├── schemas.py         # Pydantic schemas
│   └── requirements.txt    # Dependencies
├── frontend/              # React application
│   ├── src/               # React components
│   ├── package.json       # Dependencies
│   └── vite.config.js     # Build config
└── data/                  # Local data (SQLite, images)
```

---

## 🚨 Troubleshooting

| Problem | Solution |
|---------|----------|
| **"Module not found"** | `pip install -r backend/requirements.txt --upgrade` |
| **Port 8000 in use** | `lsof -i :8000` or `netstat -ano \| find "8000"` then kill process |
| **Frontend won't load** | `cd frontend && npm install && npm cache clean --force` |
| **Database locked** | `rm data/issues.db` (for SQLite development) |
| **API returns 401** | Check `.env` file, ensure FRONTEND_URL matches |

---

## 🎓 Next Steps

1. **Read** [ARCHITECTURE.md](ARCHITECTURE.md) - understand system design
2. **Explore** API docs at `http://127.0.0.1:8000/docs`
3. **Try** different detectors: `/api/detect-*` endpoints
4. **Deploy** using [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
5. **Contribute** by reading [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 📞 Need Help?

- 📖 Check the [docs/](docs/) directory
- 🐛 Open an issue on GitHub
- 💬 Check existing issues for solutions
- 🤝 Ask in discussions

---

## ✅ Success Checklist

- [ ] Backend running on http://127.0.0.1:8000
- [ ] Frontend running on http://localhost:5173
- [ ] API docs visible at http://127.0.0.1:8000/docs
- [ ] Can upload and detect civic issues
- [ ] Database has created `data/issues.db`

🎉 **You're all set! Start reporting civic issues!**
