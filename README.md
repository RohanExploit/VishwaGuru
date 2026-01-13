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

## Running Locally

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

## Deployment to Firebase

VishwaGuru can be deployed fullstack on Firebase using **Firebase Hosting** (for the frontend) and **Cloud Functions** (for the backend).

### Prerequisites

1.  Install Firebase CLI:
    ```bash
    npm install -g firebase-tools
    ```
2.  Login to Firebase:
    ```bash
    firebase login
    ```

### Deployment Steps

1.  **Initialize Project** (if not already done, or to select your project):
    ```bash
    firebase init
    ```
    - Select **Hosting** and **Functions**.
    - Choose "Use an existing project" or create a new one.
    - Select **Python** for Functions language.
    - **Important**: The project is already configured with `firebase.json` and `.firebaserc`. You might skip initialization if you just want to set the project alias:
      ```bash
      firebase use --add
      ```

2.  **Build Frontend**:
    ```bash
    cd frontend
    npm run build
    cd ..
    ```

3.  **Deploy**:
    ```bash
    firebase deploy
    ```

    This command will:
    - Build the functions source by copying `backend` and `data` into `functions/`.
    - Deploy the backend as a Firebase Cloud Function (Gen 2).
    - Deploy the `frontend/dist` folder to Firebase Hosting.
    - Set up rewrites so API calls go to the function and other routes go to the React app.

### Environment Variables

For Cloud Functions, you need to set environment variables using the Firebase CLI:

```bash
firebase functions:config:set \
  app.telegram_bot_token="YOUR_TOKEN" \
  app.gemini_api_key="YOUR_KEY" \
  app.database_url="YOUR_POSTGRES_URL"
```
*Note: Firebase Gen 2 functions use `.env` files or Google Secret Manager. The `functions:config:set` is for Gen 1. For Gen 2, it's recommended to use `.env` inside `functions/` or Secret Manager.*

**Recommended for Gen 2:**
Create `functions/.env` before deploying (DO NOT COMMIT THIS FILE):
```env
TELEGRAM_BOT_TOKEN=...
GEMINI_API_KEY=...
DATABASE_URL=...
```

## Tech Stack

*   **Frontend**: React, Vite, Tailwind CSS
*   **Backend**: Python, FastAPI, SQLAlchemy, Pydantic
*   **Database**: SQLite (Dev), PostgreSQL (Prod)
*   **AI**: Google Gemini (google-generativeai)
*   **Bot**: python-telegram-bot
*   **Deployment**: Firebase (Hosting + Functions), Render/Netlify (Alternative)

## License

This project is licensed under the **AGPL-3.0** License.
