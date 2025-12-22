# VishwaGuru

VishwaGuru is an open source platform empowering India's youth to engage with democracy. It uses AI to simplify contacting representatives, filing grievances, and organizing community action. Built for India's languages and governance, it turns selfies and videos into real civic impact.

## Features

- **AI-Powered Action Plans**: Generates WhatsApp messages and email drafts for civic issues using Google's Gemini API.
- **Issue Reporting**: Users can report issues via a web interface or a Telegram bot.
- **Local & Production Ready**: Supports SQLite for local development and PostgreSQL for production.
- **Modern Stack**: Built with React (Vite) and FastAPI.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.8+**
- **Node.js 18+** and **npm**
- **Git**

## Installation

### 1. Clone the Repository

```bash
git clone <repository_url>
cd vishwaguru
```

### 2. Backend Setup

The backend handles API requests, database interactions, and the Telegram bot.

1.  Create a virtual environment (in the root directory):
    ```bash
    # Linux/macOS
    python3 -m venv venv
    source venv/bin/activate

    # Windows
    python -m venv venv
    venv\Scripts\activate
    ```

2.  Install dependencies:
    ```bash
    pip install -r backend/requirements.txt
    ```

3.  **Environment Configuration**:
    Create a `.env` file in the root of the repository.

    Required Environment Variables:
    *   `TELEGRAM_BOT_TOKEN`: Token from @BotFather for the Telegram Bot.
    *   `GEMINI_API_KEY`: API Key from Google AI Studio.
    *   `DATABASE_URL`: (Optional) Connection string for PostgreSQL. Defaults to `sqlite:///./data/issues.db`.

    **Note**: You can copy the example file:
    ```bash
    cp .env.example .env
    ```
    Then edit `.env` to add your keys.

### 3. Frontend Setup

The frontend is a React application built with Vite.

1.  Navigate to the frontend directory:
    ```bash
    cd frontend
    ```

2.  Install dependencies:
    ```bash
    npm install
    ```

## Running the Application

### Start the Backend Server

From the **root directory** (with your virtual environment activated):

```bash
PYTHONPATH=backend python -m uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`.

**Note for Windows**: Use `set PYTHONPATH=backend & python -m uvicorn main:app --reload`

### Start the Frontend Development Server

Open a new terminal window:

```bash
cd frontend
npm run dev
```
The application will be accessible at `http://localhost:5173`.

### Start the Telegram Bot

The Telegram bot runs as part of the FastAPI application lifecycle, so it starts automatically when you run the backend server.

## Tech Stack

*   **Frontend**: React, Vite, Tailwind CSS
*   **Backend**: Python, FastAPI, SQLAlchemy, Pydantic
*   **Database**: SQLite (Dev), PostgreSQL (Prod)
*   **AI**: Google Gemini (google-generativeai)
*   **Bot**: python-telegram-bot

## Contributing

1.  Fork the repository.
2.  Create a new branch (`git checkout -b feature/YourFeature`).
3.  Commit your changes (`git commit -m 'Add some feature'`).
4.  Push to the branch (`git push origin feature/YourFeature`).
5.  Open a Pull Request.

## License

This project is licensed under the **AGPL-3.0** License.
