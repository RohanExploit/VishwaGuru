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

## 2025-05-30 - Session Management Anti-Pattern
**Learning:** Using `if db is not SessionLocal(): db.close()` to manage session lifecycle is flawed because `SessionLocal` is a factory, and instances will never match it. This leads to premature closure of injected sessions (e.g., from FastAPI dependencies).
**Action:** Use an `is_local_session` flag to track if the session was created within the method and should be closed by it.

## 2025-05-30 - O(1) Blockchain Hash Lookup
**Learning:** Calculating a blockchain-style hash chain requires finding the previous record's hash. A naive DB scan is O(log N) with indexes, but high-concurrency follow operations can be optimized.
**Action:** Implement an in-memory thread-safe cache for the last hash of each grievance to achieve O(1) lookup during follower creation, falling back to DB on cache miss.

## 2025-07-15 - Fast Bounding Box Pre-filter
**Learning:** Calculating great circle distance (Haversine) for every issue against a target location is computationally expensive (O(N) with heavy math ops like sin, cos, atan2). In high-traffic aggregations, this can become a bottleneck.
**Action:** Use a fast bounding box pre-filter (`get_bounding_box` with a 5% epsilon) to quickly discard issues that are definitely outside the search radius before running the expensive exact haversine distance calculation.
## 2025-05-30 - N+1 Query in Escalation Engine
**Learning:** The `EscalationEngine.evaluate_and_escalate_grievances` fetches grievances that need evaluation, and subsequent loops access `grievance.jurisdiction.level`. Since `jurisdiction` is evaluated lazily, this causes an N+1 query problem during the periodic cron job.
**Action:** Use `joinedload(Grievance.jurisdiction)` in `_get_grievances_for_evaluation` to eager-load the jurisdiction and eliminate the bottleneck.
