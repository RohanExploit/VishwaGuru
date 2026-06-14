import sys
import os
import logging
from pathlib import Path
from sqlalchemy.orm import Session

# Add project root to path
current_file = Path(__file__).resolve()
# backend/scheduler/daily_refinement_job.py -> backend/scheduler -> backend -> root
repo_root = current_file.parent.parent.parent
sys.path.insert(0, str(repo_root))

from backend.database import SessionLocal
from backend.civic_intelligence import civic_intelligence_engine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_daily_job():
    logger.info("Initializing daily refinement job...")
    db: Session = SessionLocal()
    try:
        result = civic_intelligence_engine.refine_daily(db)
        logger.info(f"Daily refinement job completed successfully. Index Score: {result.get('index_score')}")
    except Exception as e:
        logger.error(f"Daily refinement job failed: {e}", exc_info=True)
    finally:
        db.close()

if __name__ == "__main__":
    run_daily_job()
