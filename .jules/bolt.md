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
## 2024-07-13 - Scratchpad Files and Test Runners
**Learning:** Temporary scratchpad files (like `test_spatial.py` or `test_perf.py`) created in the repository root will be automatically discovered by test runners like `pytest` because they start with `test_`. If these files contain top-level execution code (like creating arrays of 100k items), they will block test suites and pollute standard output.
**Action:** Always clean up temporary files immediately after use (e.g. `rm test_perf.py`) before running project test suites or requesting code review.

## 2024-07-13 - Haversine Distance Optimization
**Learning:** Calculating `haversine_distance` for every point in a large dataset is O(N) and extremely slow due to repeated trigonometric functions (`math.sin`, `math.cos`, etc.).
**Action:** For spatial radius queries, always apply a cheap bounding box pre-filter first (e.g., `get_bounding_box` with a 5% epsilon for safety). This reduces the complexity to O(N) fast arithmetic checks + O(K) slow trigonometric functions, where K << N.
