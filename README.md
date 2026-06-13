# 🌍 VishwaGuru - AI-Powered Civic Engagement Platform

> **Empowering India's citizens to report, verify, and resolve civic issues through AI-powered intelligence and blockchain verification**

VishwaGuru is a comprehensive platform for civic issue reporting and resolution, built with modern AI/ML technologies, featuring distributed verification, multi-language support, and real-time field officer coordination.

---

## ✨ Core Features

### 📍 Issue Reporting & Detection
- **Multi-Category Detection**: 15+ civic issue detectors (potholes, garbage, vandalism, floods, infrastructure, noise, animals, parking, streetlights, fires, trees, pests, blocked roads, safety hazards, construction)
- **AI-Powered Analysis**: Automatic severity assessment, categorization, and priority scoring
- **Spatial Deduplication**: Smart detection of nearby/duplicate issues within configurable radius
- **Image Analysis**: Advanced YOLO-based object detection + HuggingFace CLIP for semantic understanding
- **Smart Scanner**: One-tap detection for multiple issue types simultaneously

### 🎤 Voice & Language
- **Multi-Language Support**: Hindi, Bengali, Telugu, Marathi, Tamil, Gujarati, Kannada, Malayalam, Punjabi, and more
- **Voice Submission**: Report issues via audio in your preferred regional language
- **Real-Time Transcription**: Speech-to-text powered by SpeechRecognition
- **Translation Engine**: Automatic English ↔ Regional Language translation

### 🔐 Resolution Verification & Blockchain
- **Proof-of-Resolution Tokens**: Time-limited, location-verified tokens for resolution evidence
- **Geofencing Validation**: GPS verification within configurable radius (default 200m)
- **Blockchain Integrity**: Immutable audit logs with cryptographic signatures
- **Duplicate Detection**: Prevents submission of identical evidence for different grievances
- **Authority Sign-Off**: Resolving authority confirms and verifies resolution evidence

### 📊 Civic Intelligence & Analytics
- **Daily Refinement Engine**: Machine learning-based trend analysis and pattern detection
- **Adaptive Weights**: Dynamic scoring algorithm that learns from resolution history
- **Real-Time Dashboard**: Live statistics on issue distribution, resolution rates, response times
- **Leaderboard**: Citizen contribution rankings and impact metrics
- **Civic Insights**: Predictive analytics for emerging problem areas

### 🚑 Field Officer Management
- **Check-In System**: Real-time GPS tracking of field officers
- **Geofencing Alerts**: Automatic notifications when officers reach incident locations
- **Visit History**: Complete record of officer visits with timestamps and geo-coordinates
- **Mobile Workflows**: Offline-capable mobile forms for field operations

### 🏛️ Government Integration
- **MLA Locator**: Find Maharashtra Legislative Assembly representatives by pincode
- **Jurisdiction Mapping**: Automatic routing to correct government departments
- **SLA Management**: Track Service Level Agreements for different issue categories
- **Escalation Engine**: Automatic escalation with customizable thresholds
- **Grievance Tracking**: End-to-end grievance status monitoring

### 🤖 AI Services
- **Google Gemini Integration**: Advanced text generation for action plans
- **HuggingFace Models**: CLIP for image understanding, Llama for text generation
- **Local ML**: Optional CPU-based inference for privacy and offline capability
- **Fallback Chain**: Graceful degradation - Gemini → HuggingFace → Mock services
- **RAG Service**: Retrieval-Augmented Generation for civic policies

### 📲 User Engagement
- **Multi-Platform**: Web, PWA (Progressive Web App), Telegram Bot
- **Push Notifications**: Real-time updates on issue status changes
- **Offline Support**: Service Worker + IndexedDB for offline functionality
- **Dark Mode**: Full dark theme support for accessibility

---

## 🏗️ Architecture

### Backend Services (11 Modular Routers)
```
/api/issues         → Issue CRUD, spatial queries, voting
/api/detection      → ML-based issue detection endpoints
/api/grievances     → Grievance lifecycle management
/api/utility        → Helper endpoints (stats, geolocation)
/api/auth           → User authentication & authorization
/admin              → Admin dashboard & stats
/api/analysis       → Data analysis & trends
/api/voice          → Voice transcription & language translation
/api/field_officer  → Field officer check-in & geofencing
/api/hf             → Hugging Face AI text generation
/api/resolution-proof → Blockchain-based resolution verification
```

### Database Schema
- **Users**: Role-based access control (user, official, admin)
- **Issues**: Civic reports with geospatial indexing
- **Grievances**: Escalated issues with SLA tracking
- **ResolutionEvidence**: Verified proof-of-resolution with audit logs
- **EvidenceAuditLog**: Immutable audit trail for compliance
- **FieldOfficerVisits**: GPS-verified officer visits
- **PushSubscriptions**: PWA notification registry

### AI/ML Pipeline
```
Upload Image
    ↓
Validation & EXIF Stripping
    ↓
YOLO Detection (Ultralytics)
    ↓
CLIP Semantic Understanding (HuggingFace)
    ↓
Priority Engine (Adaptive Weights)
    ↓
Civic Intelligence Refinement
    ↓
Action Plan Generation (Gemini/HF/Mock)
```

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | React 19, React Router 7, Vite, Tailwind CSS | Modern SPA with code-splitting |
| **Backend** | FastAPI, SQLAlchemy, Pydantic | Async REST API with ORM |
| **Database** | SQLite (dev), PostgreSQL (prod) | Persistent storage with spatial indexing |
| **ML/AI** | Gemini, HuggingFace, YOLO, CLIP | Image/text analysis & generation |
| **Voice** | SpeechRecognition, Googletrans | Transcription & translation |
| **Messaging** | python-telegram-bot | Telegram bot integration |
| **Storage** | File system, optional S3 | Issue images & audio |
| **Deployment** | Render, Netlify, Neon | Cloud-native stack |
| **PWA** | vite-plugin-pwa, Service Workers | Offline-first functionality |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- Git

### Backend Setup
```bash
# Clone repository
git clone https://github.com/RohanExploit/VishwaGuru.git
cd VishwaGuru

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or: venv\Scripts\activate  # Windows

# Install backend dependencies
pip install -r backend/requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Start backend
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

### Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
# Opens at http://localhost:5173
```

### Required Environment Variables
```env
# API Keys
TELEGRAM_BOT_TOKEN=your_bot_token
GEMINI_API_KEY=your_gemini_key
HF_TOKEN=your_huggingface_token

# Database (defaults to SQLite for local dev)
DATABASE_URL=sqlite:///./data/issues.db

# Frontend
FRONTEND_URL=http://localhost:5173

# Optional: Production Database
# DATABASE_URL=postgresql://user:pass@host/dbname

# Optional: Hugging Face Text Generation
HF_TEXT_API_URL=https://router.huggingface.co/featherless-ai/v1/completions
HF_TEXT_MODEL=meta-llama/Meta-Llama-3-8B-Instruct

# Optional: Local ML Configuration
USE_LOCAL_ML=true
LOCAL_ML_DEVICE=cpu
LOCAL_ML_QUANTIZE=false
```

### Health Check
```bash
# Backend
curl http://127.0.0.1:8000/health

# Frontend
http://localhost:5173
```

---

## 📦 API Endpoints (92 Total)

### Issues Management
- `POST /api/issues` - Create new issue
- `GET /api/issues/{id}` - Get issue details
- `GET /api/issues/nearby` - Find nearby issues
- `POST /api/issues/{id}/vote` - Upvote issue
- `POST /api/issues/{id}/status` - Update status

### Detection
- `POST /api/detect-pothole` - Detect potholes
- `POST /api/detect-garbage` - Detect garbage
- `POST /api/detect-vandalism` - Detect vandalism
- `POST /api/detect-flooding` - Detect floods
- `POST /api/detect-infrastructure` - Detect infrastructure issues
- `POST /api/detect-traffic-sign` - Detect traffic signs
- ... and 30+ more detection endpoints

### Voice & Language
- `POST /api/voice/transcribe` - Convert audio to text
- `POST /api/voice/issue/create` - Create issue via voice
- `POST /api/voice/translate` - Translate text

### Resolution Proof
- `POST /api/resolution-proof/token/generate` - Generate proof token
- `POST /api/resolution-proof/evidence/submit` - Submit resolution evidence
- `GET /api/resolution-proof/audit/{grievance_id}` - Get audit trail

### Field Officer
- `POST /api/field_officer/checkin` - Officer check-in
- `GET /api/field_officer/visits/{officer_id}` - Get visit history
- `POST /api/field_officer/geofence/validate` - Validate geofence

### Admin
- `GET /admin/users` - List users
- `GET /admin/stats` - System statistics

### Civic Intelligence
- `GET /api/analysis/civic-intelligence` - Get civic insights
- `GET /api/analysis/trends` - Get trend analysis

---

## 📚 Documentation

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Detailed system design and data flow
- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Production deployment steps
- **[BACKEND_DEPLOYMENT_CHECKLIST.md](BACKEND_DEPLOYMENT_CHECKLIST.md)** - Backend-specific deployment
- **[CIVIC_INTELLIGENCE.md](CIVIC_INTELLIGENCE.md)** - Civic intelligence engine details
- **[VOICE_LANGUAGE_FEATURE.md](VOICE_LANGUAGE_FEATURE.md)** - Voice & language feature guide
- **[FIELD_OFFICER_CHECKIN_FEATURE.md](FIELD_OFFICER_CHECKIN_FEATURE.md)** - Field officer workflows
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Contribution guidelines

---

## 🔄 Development Workflow

### Local Testing
```bash
# Backend tests
python -m pytest backend/tests/ -v

# Frontend tests
npm run test

# Build frontend
npm run build

# Type checking
npm run type-check
```

### Migrations
```bash
# Database migrations are applied automatically on startup
# For manual migration:
python -c "from backend.init_db import migrate_db; migrate_db()"
```

---

## 🐛 Troubleshooting

### Backend won't start
- Check `.env` configuration
- Verify API keys are valid
- Try SQLite: `DATABASE_URL=sqlite:///./data/issues.db`
- Check logs: `tail -f backend.log`

### Frontend build fails
- Clear node_modules: `rm -rf node_modules && npm install`
- Clear cache: `npm cache clean --force`
- Check Node version: `node -v` (should be 18+)

### Database errors
- For SQLite (dev): `rm -f data/issues.db` to reset
- For PostgreSQL: Verify connection string and database exists
- Run migrations: `python backend/init_db.py`

### Missing modules
```bash
# Reinstall dependencies
pip install -r backend/requirements.txt --upgrade
npm ci  # Use lock file for exact versions
```

---

## 📊 Performance Metrics

- **API Response Time**: < 200ms (p95) for detection endpoints
- **Database Queries**: Indexed spatial queries in < 50ms
- **Image Processing**: < 2s for YOLO + CLIP pipeline
- **Frontend Bundle**: 816KB (minified, before gzip)
- **Lighthouse Score**: 92+ (performance), 98 (accessibility)

---

## 🔐 Security Features

- ✅ Role-based access control (RBAC)
- ✅ JWT token authentication
- ✅ HTTPS-ready (production deployment)
- ✅ EXIF data stripping from images
- ✅ Input validation on all endpoints
- ✅ Rate limiting on API endpoints
- ✅ Blockchain-based resolution verification
- ✅ Audit logging for compliance

---

## 📈 Deployment

### Quick Deployment (Render + Netlify + Neon)

1. **Backend** → Render
```bash
git push  # Automatically deploys on push
```

2. **Frontend** → Netlify
```bash
npm run build
# Connect GitHub repo to Netlify for auto-deploy
```

3. **Database** → Neon PostgreSQL
```env
DATABASE_URL=postgresql://user:pass@...neon.tech/...
```

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed steps.

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create feature branch: `git checkout -b feature/your-feature`
3. Commit changes: `git commit -m "Add your feature"`
4. Push branch: `git push origin feature/your-feature`
5. Open Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

---

## 📄 License

GNU Affero General Public License v3.0 (AGPL-3.0)

This ensures all modifications to the platform are shared back with the community.

---

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)
![React](https://img.shields.io/badge/React-19-61dafb?style=flat-square&logo=react)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?style=flat-square&logo=postgresql)
![License](https://img.shields.io/badge/License-AGPL--3.0-green?style=flat-square)

**Made with ❤️ to empower civic engagement across India**

[🌐 Website](#) • [📖 Docs](ARCHITECTURE.md) • [💬 Issues](#) • [🤝 Contribute](#)

</div>
