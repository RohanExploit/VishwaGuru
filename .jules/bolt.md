## 2024-05-23 - Blocking Async Operations
**Learning:** In FastAPI, `async def` endpoints run on the main event loop. Calling synchronous, blocking operations (like external API calls or heavy computation) directly within these endpoints blocks the entire server, preventing it from handling other requests.
**Action:** Always use asynchronous versions of I/O bound libraries (e.g., `await model.generate_content_async`) or run synchronous blocking code in a thread pool using `run_in_executor` to keep the event loop responsive.

## 2024-05-25 - Blocking DB in Async Telegram Bot
**Learning:** `python-telegram-bot` handlers are `async` and run on the event loop. Executing synchronous SQLAlchemy `db.commit()` calls directly inside a handler blocks the loop, freezing the bot (and any shared process like FastAPI).
**Action:** Offload synchronous DB operations to a thread using `asyncio.to_thread` (standard lib) instead of `fastapi.concurrency` if you want to keep the bot code generic and independent of the web framework.
