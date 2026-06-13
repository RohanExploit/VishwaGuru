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

## 2026-02-04 - Redundant Image Processing Cycles
**Learning:** Performing validation, resizing, and EXIF stripping as discrete steps in an image pipeline causes multiple redundant Decode-Process-Encode cycles. This is particularly expensive in cloud environments with limited CPU.
**Action:** Unify all image transformations into a single pass (`process_uploaded_image`) to ensure the image is only decoded and encoded once.

## 2026-02-05 - Leaderboard Aggregation Caching
**Learning:** Aggregation queries (`COUNT`, `SUM`, `GROUP BY`) on the primary application tables grow O(N) with the number of reports. On high-traffic civic platforms, these are frequent bottlenecks.
**Action:** Implement short-lived (5 min) caching for leaderboard results. Use database-level aggregations and column selection (`db.query(cols)`) instead of loading full model instances.

## 2026-02-05 - Schema Inheritance vs Redefinition
**Learning:** Redefining similar schemas (e.g., `IssueSummaryResponse` vs `IssueResponse`) leads to maintenance overhead and potential inconsistencies in API responses.
**Action:** Use Pydantic inheritance to define a base summary schema and extend it for detailed views, ensuring consistent data structures across the app.

## 2026-02-06 - Column Projection vs Full ORM Loading
**Learning:** Loading full SQLAlchemy model instances for list views or spatial checks is significantly slower and more memory-intensive than selecting only required columns, especially when tables contain large JSON or Text fields.
**Action:** Use `db.query(Model.col1, Model.col2)` for read-heavy list endpoints and spatial candidate searches. Note that projected results are immutable `Row` objects, so use `db.query(Model).filter(...).update()` for atomic modifications.

## 2026-02-07 - Transaction Consolidation for Performance
**Learning:** Performing multiple `db.commit()` calls in a single endpoint handler increases latency due to multiple round-trips and disk I/O. Using `db.flush()` allows intermediate results (like atomic increments) to be available for queries in the same transaction without the cost of a full commit.
**Action:** Consolidate multiple database updates into a single transaction. Use `db.flush()` when you need to query the database for values updated via `update()` before the final commit.

## 2026-02-08 - Return Type Consistency in Utilities
**Learning:** Inconsistent return types in shared utility functions (like `process_uploaded_image`) can cause runtime crashes across multiple modules, especially when some expect tuples and others expect single values. This can lead to deployment failures that are hard to debug without full integration logs.
**Action:** Always maintain strict return type consistency for core utilities. Use type hints and verify all call sites when changing a function's signature. Ensure that performance-oriented optimizations (like returning multiple processed formats) are applied uniformly.

## 2026-02-10 - Serialization Caching vs Object Caching
**Learning:** Caching raw Python objects (like SQLAlchemy models or Pydantic instances) in a high-traffic API still incurs significant overhead because FastAPI/Pydantic must re-validate and re-serialize the data on every request.
**Action:** Serialize data to a JSON string BEFORE caching. On cache hits, return a raw `fastapi.Response` with `media_type="application/json"`. This bypasses the validation layer and is measurably faster (2-3x).

## 2026-02-10 - Group-By for Multi-Count Statistics
**Learning:** Executing multiple `count()` queries with different filters (e.g., for different statuses) causes redundant database scans and network round-triPS.
**Action:** Use a single SQL `GROUP BY` query to fetch counts for all categories/statuses at once, then process the results in Python.

## 2026-02-11 - O(1) Blockchain Verification
**Learning:** Verifying the integrity of a blockchain-style chain by querying the database for the previous record's hash on every check is inefficient and adds unnecessary latency.
**Action:** Store the `previous_integrity_hash` directly in the record during creation. This enables O(1) single-record integrity checks without additional database lookups. Use a thread-safe cache to keep the most recent hash in memory to further optimize the creation path.

## 2026-02-11 - Multi-Metric Aggregate Queries
**Learning:** Executing multiple separate `count()` queries to gather system statistics results in multiple database round-trips and redundant table scans.
**Action:** Use a single SQLAlchemy query with `func.count()` and `func.sum(case(...))` to calculate all metrics in one go. This reduces network overhead and allows the database to perform calculations in a single pass.

## 2025-02-13 - Substring pre-filtering for regex optimization
**Learning:** In hot paths (like `PriorityEngine._calculate_urgency`), executing pre-compiled regular expressions (`re.search`) for simple keyword extraction or grouping (e.g., `\b(word1|word2)\b`) is significantly slower than simple Python substring checks (`in text`). The regex engine execution overhead in Python adds up in high-iteration loops like priority scoring.
**Action:** Always consider pre-extracting literal keywords from simple regex patterns and executing a quick `any(k in text for k in keywords)` pre-filter. Only invoke `regex.search` if the pre-filter passes, avoiding the expensive regex operation on texts that obviously do not match.

## 2025-02-13 - API Route Prefix Consistency
**Learning:** Inconsistent application of `/api` prefixes between `main.py` router mounting and test suite request paths can lead to 404 errors during testing, even if the logic is correct. This is especially prevalent when multiple agents work on the same codebase with different assumptions about global prefixes.
**Action:** Always verify that `app.include_router` in `backend/main.py` uses `prefix="/api"` if the test suite (e.g., `tests/test_blockchain.py`) expects it. If a router is mounted without a prefix, ensure tests are updated or the prefix is added to `main.py` to maintain repository-wide consistency.

## 2026-03-05 - Scratchpad File Cleanup
**Learning:** Leaving scratchpad files like Python test scripts or benchmarking shell scripts pollutes the repository and will cause code reviews to fail. Even if the optimization works, the PR must be clean and only contain relevant application changes.
**Action:** Always clean up generated development files, scripts, and temporary databases using `rm` before requesting a code review or submitting a PR.

## 2026-03-05 - Transaction Consolidation with Blockchain Chaining
**Learning:** Consolidating multiple database operations into a single transaction reduces disk I/O and latency. However, when using blockchain-style hash chaining with in-memory caches, global caches MUST NOT be updated until after a successful commit to prevent poisoning on rollbacks. Intermediate chaining during the transaction must be handled manually or via a separate local tracking mechanism.
**Action:** Consolidate multiple `db.commit()` calls into one using `db.flush()` for intermediate IDs. Track generated hashes locally and update global `ThreadSafeCache` only after `db.commit()` succeeds.

## 2026-04-17 - ORM Counting vs func.count().scalar()
**Learning:** Using `db.query(Model).filter(...).count()` can be slower and have more ORM overhead than `db.query(func.count(Model.id)).filter(...).scalar() or 0` or doing an early `.first()` exit.
**Action:** When counting records or verifying existence, prefer early `.first()` exits combined with `func.count().scalar()` for performance in high-traffic APIs.

## 2026-04-20 - Async File I/O in Voice Submission
**Learning:** Saving audio recordings (up to 10MB) synchronously in a FastAPI async endpoint blocks the main event loop, significantly increasing tail latency for all concurrent users during high-traffic periods.
**Action:** Wrap blocking synchronous File I/O operations like `f.write()` in `run_in_threadpool` to offload them to a separate thread, keeping the event loop responsive for other requests.

## 2026-03-05 - Transaction Consolidation with Blockchain Chaining
**Learning:** Consolidating multiple database operations into a single transaction reduces disk I/O and latency. However, when using blockchain-style hash chaining with in-memory caches, global caches MUST NOT be updated until after a successful commit to prevent poisoning on rollbacks. Intermediate chaining during the transaction must be handled manually or via a separate local tracking mechanism.
**Action:** Consolidate multiple `db.commit()` calls into one using `db.flush()` for intermediate IDs. Track generated hashes locally and update global `ThreadSafeCache` only after `db.commit()` succeeds.

## 2026-05-15 - Serialization Caching Bypass
**Learning:** Caching raw Python objects (like SQLAlchemy models or Pydantic instances) in a high-traffic API still incurs significant overhead because FastAPI/Pydantic must re-validate and re-serialize the data on every request.
**Action:** Serialize data to a JSON string using `json.dumps()` BEFORE caching. On cache hits, return a raw `fastapi.Response(content=..., media_type="application/json")`. This bypasses the validation and serialization layer, resulting in significant performance gains (up to 50x in benchmarks).

## 2026-05-16 - Pre-processing for RAG Retrieval
**Learning:** In RAG (Retrieval-Augmented Generation) systems with static or semi-static policy datasets, performing tokenization, regex substitution, and string formatting inside the retrieval loop is a significant bottleneck that scales with the number of policies.
**Action:** Move all deterministic operations (tokenization, formatting, regex matching prep) to a one-time initialization step to ensure the retrieval hot-path only performs necessary set intersections and similarity calculations.

## 2026-05-18 - Jaccard Similarity Optimization via Set Arithmetic
**Learning:** In retrieval loops calculating Jaccard similarity (e.g. RAG), explicitly building a union set `A.union(B)` is expensive due to memory allocation and population.
**Action:** Use the inclusion-exclusion principle $|A \cup B| = |A| + |B| - |A \cap B|$ to calculate union size in O(1) arithmetic time after calculating the intersection. Pre-calculate $|B|$ (token count) to further reduce overhead. Use `isdisjoint()` for fast early-exit.

## 2026-05-20 - Joined Queries for Integrity Verification
**Learning:** Performing multiple sequential database queries to verify cryptographically chained records (e.g., fetching a record and then its associated token/metadata from another table) introduces unnecessary latency and increases database load.
**Action:** Consolidate associated data retrieval into a single SQL `JOIN` query within the verification hot-path. This reduces database round-trips and improves end-to-end latency for blockchain-style integrity checks.

## 2026-06-02 - Keyword Extraction Optimization
**Learning:** In bulk text analysis (like TrendAnalyzer), calling string methods like `.lower()` on thousands of small objects individually is significantly slower than joining them into a single string and calling the method once. Additionally, pre-compiling simple word-splitting regexes (`\w+`) provides a measurable boost over repeated `re.findall` calls with complex boundary markers.
**Action:** Always batch string normalization operations before tokenization in high-volume processing paths. Pre-compile word-extraction regexes at the class level.
