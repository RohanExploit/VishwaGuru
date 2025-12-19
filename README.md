# VishwaGuru

**Civic Action, Simplified.**

VishwaGuru is a lightweight, full-stack civic action platform designed for the Global South. It helps citizens understand who is responsible for their local issues (roads, water, safety) and empowers them to take action via WhatsApp, Email, or Telegram, powered by AI.

## Features

*   **Who is Responsible?** - Instant mapping of issues to authorities (e.g., Road -> Municipal Corporation).
*   **Issue Reporting (Web):** Upload a photo and description to generate an AI-drafted complaint.
*   **Action Generator:** Get ready-to-send WhatsApp messages and Email drafts.
*   **Telegram Bot:** Report issues directly via Telegram (User -> Bot -> Database).
*   **Low Resource:** No heavy cloud infrastructure, no paid APIs (optional Gemini), works on low bandwidth.

## Tech Stack

*   **Frontend:** React + Vite + Tailwind CSS
*   **Backend:** FastAPI (Python)
*   **Database:** SQLite (Local) / PostgreSQL (Production)
*   **AI:** Google Gemini (Generative AI)
*   **Bot:** Python Telegram Bot

## Deployment (Render.com)

**Note:** We use the "Web Service" method to avoid credit card requirements for Blueprints.

1.  **Push** this repository to your GitHub.
2.  **Log in** to [Render.com](https://dashboard.render.com).
3.  Click **New +** -> **Web Service**.
4.  **Connect** your GitHub repository.
5.  **Configure** the service:
    *   **Name:** `vishwaguru` (or any name)
    *   **Runtime:** `Python 3`
    *   **Build Command:** `./render-build.sh`
    *   **Start Command:** `python -m uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
    *   **Instance Type:** `Free`
6.  **Environment Variables** (Add these in the "Environment" tab):
    *   `PYTHON_VERSION` = `3.12.12`
    *   `TELEGRAM_BOT_TOKEN` = `your_telegram_bot_token`
    *   `GEMINI_API_KEY` = `your_gemini_api_key`
    *   *(Optional)* `DATABASE_URL` = `internal_connection_string_of_render_postgres` (If you create a separate Free Postgres database). If skipped, it uses ephemeral SQLite (data resets on restart).
7.  Click **Create Web Service**.

## Local Development

1.  **Backend:**
    ```bash
    pip install -r backend/requirements.txt
    python -m uvicorn backend.main:app --reload
    ```
2.  **Frontend:**
    ```bash
    cd frontend
    npm install
    npm run dev
    ```

## License
AGPL-3.0
