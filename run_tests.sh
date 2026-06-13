#!/bin/bash
python -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt pytest pytest-asyncio pytest-mock
TELEGRAM_BOT_TOKEN=test PYTHONPATH=. pytest backend/tests/
