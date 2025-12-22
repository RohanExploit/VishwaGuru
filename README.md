# VishwaGuru

**Civic Action, Simplified.**

VishwaGuru is a lightweight, full-stack civic action platform designed for the Global South. It helps citizens understand who is responsible for their local issues (roads, water, safety) and empowers them to take action via WhatsApp, Email, or Telegram, powered by AI.

## Features

*   **Who is Responsible?** - Instant mapping of issues to authorities (e.g., Road -> Municipal Corporation).
*   **Issue Reporting (Web):** Upload a photo and description to generate an AI-drafted complaint.
*   **Action Generator:** Get ready-to-send WhatsApp messages and Email drafts.
*   **Telegram Bot:** Report issues directly via Telegram (User -> Bot -> Database).
*   **Google Auth:** Optional sign-in to track identity (Client-side integration).
*   **Android App:** Capacitor-wrapped Web App for native Android experience.
*   **Low Resource:** No heavy cloud infrastructure, no paid APIs (optional Gemini), works on low bandwidth.

## Tech Stack

*   **Frontend:** React + Vite + Tailwind CSS + Capacitor (Android)
*   **Backend:** FastAPI (Python) + SQLAlchemy
*   **Database:** SQLite (Local) / PostgreSQL (Production)
*   **AI:** Google Gemini (Generative AI)
*   **Bot:** Python Telegram Bot

## Prerequisites

*   Node.js (v18+)
*   Python (3.12+)
*   Git

## Local Installation

1.  **Clone the repo:**
    ```bash
    git clone https://github.com/RohanExploit/VishwaGuru.git
    cd VishwaGuru
    ```

2.  **Backend Setup:**
    ```bash
    # Create virtual environment (optional but recommended)
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate

    # Install dependencies
    pip install -r backend/requirements.txt

    # Set Environment Variables (Create a .env file or export)
    export TELEGRAM_BOT_TOKEN="your_bot_token"
    export GEMINI_API_KEY="your_gemini_key"

    # Run Server (from root)
    python -m uvicorn backend.main:app --reload
    ```

3.  **Frontend Setup:**
    ```bash
    cd frontend
    npm install

    # Configure Google Client ID in src/App.jsx (Replace placeholder)

    # Run Dev Server
    npm run dev
    ```

## Android Build (Capacitor)

1.  **Initialize & Sync:**
    ```bash
    cd frontend
    npm run build
    npx cap sync
    ```

2.  **Build APK:**
    *   **Option A (If you have Android Studio):**
        ```bash
        npx cap open android
        ```
        Then build via Android Studio.
    *   **Option B (CI/CD or Command Line):**
        Use Gradle wrapper in `android/` directory (requires Java/Android SDK installed).

## Deployment (Render.com)

**Note:** We use the "Web Service" method to avoid credit card requirements for Blueprints.

1.  **Push** this repository to your GitHub.
2.  **Log in** to [Render.com](https://dashboard.render.com).
3.  Click **New +** -> **Web Service**.
4.  **Connect** your GitHub repository.
5.  **Configure** the service:
    *   **Name:** `vishwaguru`
    *   **Runtime:** `Python 3`
    *   **Build Command:** `./render-build.sh`
    *   **Start Command:** `python -m uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
    *   **Instance Type:** `Free`
6.  **Environment Variables**:
    *   `PYTHON_VERSION` = `3.12.12`
    *   `TELEGRAM_BOT_TOKEN` = `...`
    *   `GEMINI_API_KEY` = `...`
    *   `DATABASE_URL` (Auto-filled if using Postgres service, else leave empty for SQLite).
7.  Click **Create Web Service**.

## License
AGPL-3.0
