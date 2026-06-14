# Backend – VishwaGuru

The backend powers all core functionality of VishwaGuru. It is built with FastAPI and serves both the web application and the Telegram bot.

## Responsibilities

- Expose REST APIs for the frontend
- Process and store civic issue submissions
- Integrate with Google Gemini for AI-generated action plans
- Run the Telegram bot within the application lifecycle
- Manage database interactions

## Tech Stack

- FastAPI
- SQLAlchemy
- Pydantic
- python-telegram-bot
- SQLite (development)
- PostgreSQL (production)

## Environment Variables

Create a `.env` file in the backend directory with the following variables:

```bash
# Required API Keys
GEMINI_API_KEY=your_gemini_api_key_here
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# Database Configuration
DATABASE_URL=sqlite:///./data/issues.db  # Development
# DATABASE_URL=postgresql://username:password@host:port/database  # Production

# Frontend URL (required for CORS)
FRONTEND_URL=https://your-frontend.netlify.app

# Application Environment
ENVIRONMENT=production
DEBUG=false

# CORS Origins (comma-separated)
CORS_ORIGINS=https://your-frontend.netlify.app
```

## Running the Backend

### Development
```bash
cd backend
pip install -r requirements.txt
PYTHONPATH=backend python -m uvicorn main:app --reload
```

### Production
```bash
cd backend
pip install -r requirements.txt
PYTHONPATH=backend python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

## API Endpoints

### Core Endpoints

- `GET /` - API root with service information
- `GET /health` - Health check endpoint
- `GET /api/stats` - Application statistics

### Issues Management

- `GET /api/issues/recent` - Get recent issues
- `POST /api/issues` - Create new issue
- `GET /api/issues/{id}` - Get specific issue
- `PUT /api/issues/{id}/vote` - Vote on issue
- `PUT /api/issues/{id}/status` - Update issue status

### AI Services

- `POST /api/chat` - Chat with civic assistant
- `POST /api/detect/{detector_type}` - Run ML detection
- `POST /api/analyze-urgency` - Analyze issue urgency

### Utility Endpoints

- `GET /api/responsibility-map` - Get responsibility mapping
- `GET /api/mh/rep-contacts` - Get Maharashtra representative contacts
- `POST /api/push/subscribe` - Subscribe to push notifications

## Deployment

### Render Deployment

1. Create a Render account at https://render.com
2. Connect your GitHub repository
3. Use the `render.yaml` file in the project root for automatic configuration
4. Set environment variables in the Render dashboard
5. Deploy and monitor logs

### Manual Deployment

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export PYTHONPATH=backend
export FRONTEND_URL=https://your-frontend.netlify.app
export GEMINI_API_KEY=your_key
export TELEGRAM_BOT_TOKEN=your_token
export DATABASE_URL=your_database_url

# Run the application
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

## Database

The application supports both SQLite (development) and PostgreSQL (production).

### SQLite Setup (Development)
```bash
# Database file will be created automatically at data/issues.db
export DATABASE_URL=sqlite:///./data/issues.db
```

### PostgreSQL Setup (Production)
Use services like Neon, Supabase, or AWS RDS:
```bash
export DATABASE_URL=postgresql://username:password@host:port/database
```

## Testing

Run the test suite:
```bash
cd backend
python -m pytest tests/
```

## API Documentation

Once the server is running, visit `http://localhost:8000/docs` for interactive API documentation powered by Swagger UI.
