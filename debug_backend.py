import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from backend.main import app
import httpx

async def test_lifespan():
    logger.info("Starting lifespan test script...")
    try:
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            logger.info("Lifespan context entered successfully!")
            response = await client.get("/health")
            logger.info(f"Health check response: {response.json()}")
    except Exception as e:
        logger.error(f"Lifespan test failed: {e}", exc_info=True)

if __name__ == "__main__":
    os.environ["ENVIRONMENT"] = "development"
    os.environ["DEBUG"] = "true"
    os.environ["USE_LOCAL_ML"] = "false"
    asyncio.run(test_lifespan())
