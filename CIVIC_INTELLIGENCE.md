# 🧠 Daily Civic Intelligence Refinement Engine

The Civic Intelligence Engine is a self-improving AI infrastructure that runs daily at midnight (UTC) to analyze civic issues, detect trends, and optimize system parameters automatically.

## 🚀 Overview

Every day at 00:00, the system:
1.  **Analyzes** all civic issues submitted in the last 24 hours.
2.  **Detects** new patterns, trending topics, and geographic clusters.
3.  **Refines** severity scoring weights based on manual overrides (adaptive learning).
4.  **Optimizes** duplicate detection thresholds based on clustering density.
5.  **Generates** a "Civic Intelligence Index" score.
6.  **Archives** a daily snapshot for transparency and auditability.

---

## ⚙️ Core Components

### 1. Trend Detection (`backend/trend_analyzer.py`)
*   **Keyword Extraction**: Identifies top 5 most common keywords (excluding stop words) from issue descriptions.
*   **Category Spikes**: Detects categories with a >50% increase in volume compared to the previous day.
*   **Geographic Clustering**: Uses DBSCAN (Density-Based Spatial Clustering of Applications with Noise) to identify hotspots where multiple issues are reported in close proximity.

### 2. Adaptive Weight Optimization (`backend/adaptive_weights.py`)
The system learns from human actions to improve its automated severity scoring.

*   **Logic**: If administrators manually upgrade the severity of issues in a specific category (e.g., changing "pothole" from Low to Critical) more than 3 times in a day, the system infers that its default weight for that category is too low.
*   **Action**: The category multiplier in `modelWeights.json` is automatically increased by 10%.
*   **Constraint**: Weights are clamped between 0.5x and 3.0x to prevent runaway values.

### 3. Duplicate Pattern Learning
The system adjusts the radius used for spatial deduplication based on the density of issues.

*   **Logic**:
    *   **High Density** (> 5 clusters): Increases search radius by 5% to better group related issues.
    *   **High Volume, No Clusters**: Increases search radius to catch potential duplicates that are slightly further apart.
    *   **Low Volume**: Decays radius slightly (by 5%) to improve precision.
*   **Implementation**: Updates `duplicate_search_radius` in `modelWeights.json`. This value is consumed by the `create_issue` endpoint for real-time deduplication.

### 4. Civic Intelligence Index (`backend/civic_intelligence.py`)
A daily score (0-100) reflecting the civic health and system responsiveness.

*   **Formula**: `Base (70) + (Resolved Issues * 2) - (New Issues * 0.5)`
*   **Insights**:
    *   **Top Emerging Concern**: The category with the highest volume.
    *   **Highest Severity Region**: The geographic center of the largest issue cluster.

---

## 📁 Data & Transparency

### Daily Snapshots
Snapshots are stored in `backend/data/dailySnapshots/YYYY-MM-DD.json`.
They contain:
*   `trends`: Top keywords, category distribution, clusters.
*   `civic_index`: The daily score and insights.
*   `weight_changes`: Audit log of any automatic weight adjustments.
*   `model_weights`: The state of weights at that time.

### Model Weights
Dynamic configuration is stored in `backend/data/modelWeights.json`.
*   `category_multipliers`: Dynamic severity weights.
*   `duplicate_search_radius`: Dynamic search radius in meters.

---

## 🛠️ Architecture

*   **Scheduler**: A lightweight `asyncio` loop in `backend/scheduler.py` triggers the job.
*   **Execution**: `CivicIntelligenceEngine.run_daily_cycle` runs in a separate thread to avoid blocking the main event loop.
*   **Persistence**: All state changes are persisted to JSON files, ensuring "Local First" architecture with no external API dependencies for core logic.
