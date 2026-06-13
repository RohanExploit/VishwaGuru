# Technical Challenges

Welcome to the VishwaGuru "Hard Mode" challenges. These tasks are designed for experienced engineers looking to make significant architectural improvements to the platform. They require deep knowledge of system design, performance optimization, and modern web technologies.

## 1. Edge AI Migration (Client-Side Detection)

**Objective:** Move the current server-side image detection (Potholes, Garbage, Vandalism) to the client-side using WebAssembly-powered inference.

**Problem:**
Currently, images are uploaded to the backend (`backend/hf_service.py`, `backend/pothole_detection.py`), where they are processed by PyTorch or Hugging Face API calls. This incurs:
-   High latency (network round-trip + server processing).
-   Privacy concerns (sending images to the server).
-   Server costs and resource usage (CPU/RAM for PyTorch models).
-   Inability to work offline.

**Challenge:**
Implement an offline-capable, in-browser detection system.
-   **Tech Stack:** TensorFlow.js, ONNX Runtime Web, or TFLite.
-   **Requirements:**
    -   Convert existing YOLO/CLIP models (or find equivalent lightweight models) to a web-friendly format (ONNX/TFJS).
    -   Run inference in a Web Worker to avoid blocking the UI thread.
    -   Use WebGL or WebGPU backend for acceleration.
    -   Maintain acceptable accuracy (>70% confidence) while keeping model size low (<10MB if possible, or lazy-loaded).
    -   Fallback to server-side API if the device is too weak or WebGL is unavailable.

## 2. Scalable Geospatial Clustering & Indexing

**Objective:** Optimize the `get_recent_issues` endpoint to handle 100,000+ concurrent data points with dynamic clustering.

**Problem:**
The current implementation (`backend/main.py`) fetches the last 10 issues or a naive list. As the dataset grows:
-   Sending thousands of coordinate points to the frontend will crash the browser or lag the map.
-   Database queries will become slow without spatial indexing.
-   The map looks cluttered.

**Challenge:**
Implement a server-side clustering algorithm that responds to map viewport bounds and zoom levels.
-   **Tech Stack:** PostgreSQL (PostGIS) or optimized Python (NumPy/Pandas/KDTree).
-   **Requirements:**
    -   **Viewport-based Querying:** Only fetch issues within the visible map bounds (`min_lat`, `max_lat`, `min_lon`, `max_lon`).
    -   **Dynamic Clustering:** Group nearby points into a single "Cluster" object based on the zoom level (e.g., at zoom level 5, one dot for a whole city; at zoom 15, individual issues).
    -   **Performance:** Response time < 200ms for 100k records.
    -   **Implementation:** Can be done via PostGIS `ST_ClusterDBSCAN` / `ST_ClusterKMeans` or a custom Grid-based aggregation in Python if using SQLite.
    -   **API Update:** Update `GET /api/issues` to accept `bbox` and `zoom` parameters.

## 3. Resilient Offline-First Sync Architecture

**Objective:** Allow users to report issues and browse the map with zero connectivity, synchronizing automatically when the connection is restored.

**Problem:**
The app currently requires an active internet connection to post issues. If a user is in a remote area with poor signal (common for reporting infrastructure issues), the upload fails.

**Challenge:**
Build a "Local-First" data layer.
-   **Tech Stack:** IndexedDB (via `idb` or `Dexie.js`), Service Workers, Background Sync API.
-   **Requirements:**
    -   **Optimistic UI:** When a user clicks "Submit", the UI updates immediately as if it succeeded, storing the request in a local queue.
    -   **Persistence:** All drafts, images, and recent map data should be cached in IndexedDB.
    -   **Synchronization Manager:** A background process (or Service Worker) that monitors network status and retries failed requests with exponential backoff.
    -   **Conflict Resolution:** Handle edge cases where the server state might differ from the local state (mostly purely additive for this app, but duplicate prevention is needed).
    -   **Image Handling:** Store image Blobs locally and upload them only when online.

---

**Submission:**
If you attempt these, please open a dedicated Pull Request with a comprehensive description of your approach. These are major changes, so discuss your design in an Issue first!
