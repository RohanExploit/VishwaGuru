#!/bin/bash
pip install -r backend/requirements.txt pytest-asyncio
TELEGRAM_BOT_TOKEN=test pytest backend/tests/
