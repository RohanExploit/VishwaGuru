# Render Deployment Guide for VishwaGuru Backend

To deploy the VishwaGuru backend on Render (especially on the Free Tier), follow these configuration settings.

## Service Configuration

- **Service Type**: Web Service
- **Runtime**: Python
- **Root Directory**: (Leave empty - use the project root)
- **Build Command**: `pip install -r backend/requirements-render.txt`
- **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`

## Environment Variables

The following environment variables are **required**:

- `GEMINI_API_KEY`: Your Google Gemini API Key.
- `TELEGRAM_BOT_TOKEN`: Your Telegram Bot Token.
- `FRONTEND_URL`: The URL of your deployed frontend (e.g., `https://your-app.netlify.app`).

The following are **optional**:

- `ENVIRONMENT`: Set to `production`.
- `HF_TOKEN`: Hugging Face Token (required for fallback AI features if local ML is disabled).
- `DATABASE_URL`: Your database connection string (e.g., Postgres). If not set, it defaults to a local SQLite database.

## Persistent Disk (Optional but recommended for SQLite)

If you are using the default SQLite database, any data will be lost when the service restarts. To persist data:

1. Go to the **Disk** tab in your Render service settings.
2. Add a Disk:
   - **Name**: `vishwaguru-data`
   - **Mount Path**: `/opt/render/project/src/data`
   - **Size**: 1 GB

## Troubleshooting

### Why use `requirements-render.txt`?
The standard `requirements.txt` contains heavy machine learning libraries (like `torch` and `ultralytics`) that exceed the memory and disk limits of the Render Free Tier. `requirements-render.txt` excludes these, and the backend is designed to automatically fall back to Hugging Face APIs.

### ModuleNotFoundError: No module named 'backend'
Ensure your **Root Directory** is NOT set to `backend`. It should be the root of the repository. The start command `uvicorn backend.main:app` expects to be run from the repository root.
