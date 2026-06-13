import os
import logging
import httpx

from backend.database import engine, Base
from backend.init_db import migrate_db
from backend.bot import start_bot_thread, stop_bot_thread
from backend.maharashtra_locator import load_maharashtra_pincode_data, load_maharashtra_mla_data
from backend.ai_factory import create_all_ai_services
from backend.ai_interfaces import initialize_ai_services
from backend.grievance_service import GrievanceService
from backend.exceptions import EXCEPTION_HANDLERS
import backend.dependencies

# Import routers
from backend.routers import issues, detection, grievances, utility

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create tables
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    migrate_db()

    app.state.http_client = httpx.AsyncClient()
    backend.dependencies.SHARED_HTTP_CLIENT = app.state.http_client
    logger.info("Shared HTTP Client initialized.")

    try:
        action_plan_service, chat_service, mla_summary_service = create_all_ai_services()
        initialize_ai_services(action_plan_service, chat_service, mla_summary_service)
        logger.info("AI services initialized.")
    except Exception as e:
        logger.error(f"Error initializing AI services: {e}", exc_info=True)

    try:
        app.state.grievance_service = GrievanceService()
        logger.info("Grievance service initialized.")
    except Exception as e:
        logger.error(f"Error initializing grievance service: {e}", exc_info=True)

    try:
        load_maharashtra_pincode_data()
        load_maharashtra_mla_data()
        logger.info("Maharashtra data pre-loaded.")
    except Exception as e:
        logger.error(f"Error pre-loading data: {e}")

    try:
        start_bot_thread()
        logger.info("Bot thread started.")
    except Exception as e:
        logger.error(f"Error starting bot: {e}")

    yield

    # Shutdown
    if hasattr(app.state, 'http_client') and app.state.http_client:
        await app.state.http_client.aclose()
        logger.info("HTTP Client closed.")

    try:
        stop_bot_thread()
        logger.info("Bot thread stopped.")
    except Exception as e:
        logger.error(f"Error stopping bot: {e}")

app = FastAPI(
    title="VishwaGuru Backend",
    description="AI-powered civic issue reporting and resolution platform",
    version="1.0.0"
    # Temporarily disable lifespan for local dev debugging
    # lifespan=lifespan
)

# Exception Handlers
for exception_type, handler in EXCEPTION_HANDLERS.items():
    app.add_exception_handler(exception_type, handler)

# CORS
frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:5173")
is_production = os.environ.get("ENVIRONMENT", "").lower() == "production"

allowed_origins = [frontend_url]
if not is_production:
    allowed_origins.extend([
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://localhost:8080",
    ])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=500)

# Include Routers
# These routers contain all the endpoints previously duplicated in main.py
app.include_router(utility.router)
app.include_router(issues.router)
app.include_router(detection.router)
app.include_router(grievances.router)
