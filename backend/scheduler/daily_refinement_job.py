import sys
import os
from pathlib import Path

# Setup path
current_file = Path(__file__).resolve()
scheduler_dir = current_file.parent
backend_dir = scheduler_dir.parent
repo_root = backend_dir.parent

if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

import logging
from backend.database import SessionLocal, engine, Base
from backend.civic_intelligence import CivicIntelligenceEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_job():
    logger.info("Starting Daily Refinement Job...")

    # Ensure tables exist (idempotent)
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        logger.warning(f"Could not create tables (might already exist or permission error): {e}")

    db = SessionLocal()
    try:
        civic_engine = CivicIntelligenceEngine()
        snapshot = civic_engine.refine_daily(db)
        logger.info(f"Job completed successfully. Snapshot saved for {snapshot['date']}")
    except Exception as e:
        logger.error(f"Job failed: {e}", exc_info=True)
    finally:
        db.close()

if __name__ == "__main__":
    run_job()
