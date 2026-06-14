import sys
import os
import logging

# Ensure project root is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from backend.database import SessionLocal
from backend.civic_intelligence import get_civic_intelligence_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting scheduled job: Daily Civic Intelligence Refinement")

    db = SessionLocal()
    try:
        engine = get_civic_intelligence_engine()
        result = engine.refine_daily(db)

        print("\n--- Civic Intelligence Report ---")
        print(f"Date: {result['date']}")
        print(f"Index Score: {result['civic_intelligence_index']['score']}")
        print(f"Emerging Concern: {result['civic_intelligence_index']['top_emerging_concern']}")
        print(f"Top Region: {result['civic_intelligence_index']['highest_severity_region']}")

        spikes = result['trends'].get('category_spikes', [])
        if spikes:
            print("\nCategory Spikes Detected:")
            for spike in spikes:
                print(f"  - {spike['category']}: {spike['growth_percent']}% increase")
        else:
            print("\nNo significant category spikes.")

        print("\nWeights optimization complete.")
        print(f"Snapshot saved to data/dailySnapshots/{result['date']}.json")
        print("-------------------------------")

    except Exception as e:
        logger.error(f"Job failed: {e}", exc_info=True)
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()
