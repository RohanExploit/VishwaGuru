## 2024-05-23 - Blocking Async Operations
**Learning:** In FastAPI, `async def` endpoints run on the main event loop. Calling synchronous, blocking operations (like external API calls or heavy computation) directly within these endpoints blocks the entire server, preventing it from handling other requests.
**Action:** Always use asynchronous versions of I/O bound libraries (e.g., `await model.generate_content_async`) or run synchronous blocking code in a thread pool using `run_in_executor` to keep the event loop responsive.

## 2024-05-25 - Blocking DB in Async Telegram Bot
**Learning:** `python-telegram-bot` handlers are `async` and run on the event loop. Executing synchronous SQLAlchemy `db.commit()` calls directly inside a handler blocks the loop, freezing the bot (and any shared process like FastAPI).
**Action:** Offload synchronous DB operations to a thread using `asyncio.to_thread` (standard lib) instead of `fastapi.concurrency` if you want to keep the bot code generic and independent of the web framework.

## 2025-05-27 - PYTHONPATH for Mixed Imports
**Learning:** When tests import both `backend.main` (treating backend as package) and `main` (treating backend as root), `PYTHONPATH` must be set to `.:backend` (or equivalent) to satisfy both import styles.
**Action:** Use `PYTHONPATH=.:backend pytest tests/` when running tests in a repo with mixed import styles.

## 2025-02-27 - UploadFile Validation Blocking
**Learning:** `UploadFile` validation using `python-magic` and file seeking is synchronous and CPU/IO bound. In FastAPI async endpoints, this blocks the event loop.
**Action:** Wrap file validation logic in `run_in_threadpool` and await it.

## 2025-02-28 - Fast Bounding Box Pre-Filter for Geospatial Haversine Searches
**Learning:** Running `haversine_distance` (which involves multiple trig functions) on large collections of points is slow. Bounding box calculation (`get_bounding_box`) combined with a quick bounding box coordinate comparison (`lat < min_lat`, etc.) avoids computing the distance entirely for points far away.
**Action:** Always pre-filter coordinate searches using a bounding box before invoking trig-heavy `haversine` distance functions.
