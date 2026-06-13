# 🌍 VishwaGuru

VishwaGuru is an AI-powered platform designed to help users analyze civic issues and generate actionable solutions using modern web technologies and AI models.

---

## ✨ Features

- 🤖 **AI-generated action plans**: Using Google Gemini to create WhatsApp messages, email drafts, and X (Twitter) posts.
- ⚡ **FastAPI-powered backend**: High-performance asynchronous API.
- 🎨 **Modern React + Vite frontend**: Responsive and user-friendly interface.
- 📱 **Telegram bot integration**: Report issues directly from your favorite messaging app.
- 🗄️ **SQLite (dev) & PostgreSQL (prod)**: Flexible database options for development and production.
- ☁️ **Cloud Native**: Designed for deployment on Netlify, Render, and Neon.
- 📍 **Spatial Deduplication**: Automatically detects nearby issues to prevent duplicates.
- 🔍 **Unified Detection**: AI-powered detection for potholes, garbage, vandalism, and more.
- 🏛️ **MLA Lookup**: Find your Maharashtra representative by pincode and file grievances.

---

## 🛠️ Project Setup (Local)

### 📥 Clone the Repository
```bash
git clone https://github.com/Ewocs/VishwaGuru.git
cd VishwaGuru
```

---

## ⚙️ Backend Setup

### Create Virtual Environment
```bash
# Linux/macOS
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### 🔐 Environment Configuration
```bash
cp .env.example .env
```

Set the following in your `.env` file:
```env
TELEGRAM_BOT_TOKEN=your_bot_token
GEMINI_API_KEY=your_api_key
DATABASE_URL=sqlite:///./data/issues.db
FRONTEND_URL=http://localhost:5173
```

---

## 🎨 Frontend Setup
```bash
cd frontend
npm install
```

---

## 🏃‍♂️ Running Locally

| Service | Command | URL |
|------|--------|-----|
| Backend | PYTHONPATH=. python -m uvicorn backend.main:app --reload | http://localhost:8000 |
| Frontend | cd frontend && npm run dev | http://localhost:5173 |

---

## 🛠️ Tech Stack

- **Frontend**: React 18+, Vite, Tailwind CSS, Lucide Icons
- **Backend**: Python 3.12+, FastAPI, SQLAlchemy, Pydantic
- **Database**: SQLite (Dev), PostgreSQL (Prod via Neon)
- **AI/ML**: Google Gemini Pro, Hugging Face Inference API (CLIP), Ultralytics (YOLO)
- **Bot**: python-telegram-bot

---

## 🏗️ Architecture

VishwaGuru follows a modern client-server architecture:

1.  **Frontend (Netlify)**: A React application that communicates with the backend via REST APIs.
2.  **Backend (Render)**: A FastAPI server that handles logic, AI integrations, and database operations.
3.  **Database (Neon)**: A serverless PostgreSQL database for persistent storage.
4.  **AI Services**: Integrates Google Gemini for text generation and Hugging Face/Local ML for image analysis.

---

## 📚 Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - Detailed system design
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Step-by-step deployment instructions
- [CONTRIBUTING.md](CONTRIBUTING.md) - Guidelines for contributors
- [backend/README.md](backend/README.md) - Backend-specific details
- [Historic Reports](docs/archived/README.md) - Archived strategies and issue reports

---

## 📄 License

GNU Affero General Public License v3.0 (AGPL-3.0)

We welcome contributions from everyone! VishwaGuru is participating in **ECWoC26 (Elite Coders Winter of Code 2026)**.

### 🎉 ECWoC26 Contributors

Looking to contribute? Check out our [ECWoC26 Issues](./ECWOC26_ISSUES.md) for:
- 🟢 **Good First Issues** for beginners
- 🟡 **Intermediate Issues** for those with some experience
- 🔴 **Advanced Issues** for experienced developers

**Quick Start:**
1. Browse issues labeled with [`ECWoC26`](https://github.com/RohanExploit/VishwaGuru/labels/ECWoC26)
2. Comment on an issue you'd like to work on
3. Wait for assignment
4. Fork and create your feature branch
5. Submit a PR using our [PR template](./.github/PULL_REQUEST_TEMPLATE.md)

### General Contribution Process

1.  Fork the repository.
2.  Create a new branch (`git checkout -b feature/YourFeature`).
3.  Commit your changes (`git commit -m 'Add some feature'`).
4.  Push to the branch (`git push origin feature/YourFeature`).
5.  Open a Pull Request.

For detailed guidelines, check out the ECWoC26 issues - particularly Issue #1 which will establish formal contributing guidelines.

## License

**Empowering India's youth to engage with democracy through AI-powered civic action** 🚀

</div>
