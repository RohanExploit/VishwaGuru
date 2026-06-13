#!/usr/bin/env python3
import sys
import os
import logging
import traceback

# Add project root to path to ensure backend modules can be imported
# This assumes the script is located at backend/scheduler/daily_refinement_job.py
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

# Set up logging before imports to capture early errors
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("DailyRefinementJob")

try:
    from backend.civic_intelligence import CivicIntelligenceEngine
    from backend.database import SessionLocal
except ImportError as e:
    logger.error(f"Failed to import backend modules. Ensure PYTHONPATH is set correctly: {e}")
    sys.exit(1)

def run_job():
    logger.info("Initializing Daily Civic Intelligence Job...")

    # Create DB session
    db = SessionLocal()

    try:
        # Instantiate the engine
        engine = CivicIntelligenceEngine(db_session=db)

        # Execute the daily refinement process
        result = engine.refine_daily()

        logger.info("Job completed successfully.")
        logger.info(f"Snapshot created for {result.get('date')}")
        logger.info(f"Civic Intelligence Index: {result.get('civic_intelligence_index', {}).get('score')}")

    except Exception as e:
        logger.error(f"Daily Refinement Job failed: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)
    finally:
        db.close()
        logger.info("Database session closed.")

if __name__ == "__main__":
    run_job()
