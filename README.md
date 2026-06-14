# 🌍 VishwaGuru

 optimize-lazy-loading-313
VishwaGuru is an AI-powered platform designed to help users analyze issues and generate actionable solutions using modern web technologies and AI models.

---

## ✨ Features

- 🤖 AI-generated action plans using Google Gemini
- ⚡ FastAPI-powered backend
- 🎨 Modern React + Vite frontend
- 📱 Telegram bot integration
- 🗄️ SQLite (dev) & PostgreSQL (prod) support
- ☁️ Flexible deployment options

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

```env
TELEGRAM_BOT_TOKEN=your_bot_token
GEMINI_API_KEY=your_api_key
DATABASE_URL=sqlite:///./data/issues.db
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
| Backend | PYTHONPATH=backend python -m uvicorn main:app --reload | http://localhost:8000 |
| Frontend | cd frontend && npm run dev | http://localhost:5173 |

### Windows Note
```bash
set PYTHONPATH=backend & python -m uvicorn main:app --reload
```

---

## ☁️ Deployment Options

- Firebase  
- Netlify + Render  
- Railway  

---

## 🛠️ Tech Stack

- React, Vite, Tailwind CSS  
- Python, FastAPI  
- SQLite, PostgreSQL  
- Google Gemini API  

---

## 📚 Documentation

- ARCHITECTURE.md  
- DEPLOYMENT_GUIDE.md  
- frontend/README.md  
- backend/README.md  

---

## 📄 License

GNU Affero General Public License v3.0 (AGPL-3.0)

<div align="center">

![VishwaGuru Banner](https://img.shields.io/badge/VishwaGuru-Civic%20Engagement-blue?style=for-the-badge&logo=github)
![License](https://img.shields.io/badge/License-AGPL--3.0-green?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.8+-blue?style=flat-square&logo=python)
![Visitors](https://visitor-badge.laobi.icu/badge?page_id=RohanExploit.VishwaGuru&style=flat-square)
![React](https://img.shields.io/badge/React-18+-61dafb?style=flat-square&logo=react)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi)
![Firebase](https://img.shields.io/badge/Firebase-FFCA28?style=flat-square&logo=firebase)

**Empowering India's youth to engage with democracy through AI-powered civic action** 🚀

[📖 Documentation](#documentation) • [🚀 Quick Start](#installation) • [🤝 Contributing](#development--contribution-guide) • [📋 Issues](https://github.com/Ewocs/VishwaGuru/issues)

---

</div>

## ✨ What is VishwaGuru?

VishwaGuru is an open source platform that **transforms civic engagement** in India. Using cutting-edge AI, it simplifies contacting representatives, filing grievances, and organizing community actions. 

> 🎯 **Mission**: Make democracy accessible to every Indian citizen through technology

---

# Contributors

- **[RohanExploit](https://github.com/RohanExploit)**  

---

## 🌟 Key Features

<table>
<tr>
<td align="center">
<img src="https://img.shields.io/badge/🤖-AI--Powered-blue?style=for-the-badge" />
<br>
<strong>AI Action Plans</strong>
<br>
Generates personalized WhatsApp messages and email drafts using Google's Gemini API
</td>
<td align="center">
<img src="https://img.shields.io/badge/📱-Multi--Platform-green?style=for-the-badge" />
<br>
<strong>Multi-Platform</strong>
<br>
Report issues via modern web interface or Telegram bot
</td>
<td align="center">
<img src="https://img.shields.io/badge/⚡-Production--Ready-orange?style=for-the-badge" />
<br>
<strong>Production Ready</strong>
<br>
SQLite for development, PostgreSQL for production
</td>
</tr>
<tr>
<td align="center">
<img src="https://img.shields.io/badge/🎨-Modern--Stack-purple?style=for-the-badge" />
<br>
<strong>Modern Stack</strong>
<br>
React + Vite frontend, FastAPI backend
</td>
<td align="center">
<img src="https://img.shields.io/badge/🌐-Indian--Focused-red?style=for-the-badge" />
<br>
<strong>India-Centric</strong>
<br>
Built for Indian languages and governance systems
</td>
<td align="center">
<img src="https://img.shields.io/badge/🔒-Open--Source-yellow?style=for-the-badge" />
<br>
<strong>Open Source</strong>
<br>
Free, transparent, and community-driven
</td>
</tr>
</table>

---

## 🏗️ Architecture & Data Flow
The content continues as it was...

