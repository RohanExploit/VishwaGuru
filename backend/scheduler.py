import asyncio
import logging
from datetime import datetime, timedelta, timezone

from backend.civic_intelligence import civic_intelligence_engine

logger = logging.getLogger(__name__)

async def run_daily_scheduler():
    """
    Runs a loop that executes the daily civic intelligence refinement at midnight UTC.
    """
    logger.info("Daily Civic Intelligence Scheduler started.")

    while True:
        now = datetime.now(timezone.utc)

        # Calculate next run time (next midnight)
        next_run = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)

        sleep_seconds = (next_run - now).total_seconds()

        logger.info(f"Next daily refinement scheduled in {sleep_seconds/3600:.1f} hours ({next_run} UTC).")

        try:
            await asyncio.sleep(sleep_seconds)

            logger.info("Running scheduled daily refinement...")

            # Run synchronous blocking code in a separate thread
            await asyncio.to_thread(civic_intelligence_engine.run_daily_cycle)

        except asyncio.CancelledError:
            logger.info("Scheduler task cancelled.")
            break
        except Exception as e:
            logger.error(f"Error in scheduler loop: {e}", exc_info=True)
            # Sleep a bit before retrying to avoid tight loop on persistent error
            await asyncio.sleep(60)

def start_scheduler():
    """
    Helper to start the scheduler as a background task.
    Should be called from FastAPI startup event.
    """
    asyncio.create_task(run_daily_scheduler())
