# TypeScript Daily Civic Intelligence Refinement Engine

## Overview
VishwaGuru's Civic Intelligence Engine is a self-improving AI system that runs daily at midnight. It operates entirely locally using Node.js and SQLite, analyzing civic issues, detecting trends, and optimizing the system's severity scoring logic based on real-world patterns.

## Architecture
The engine is composed of the following TypeScript modules:
1.  **PriorityEngine (`services/priorityEngine.ts`):** Calculates severity and urgency scores based on predefined keywords and dynamic multipliers from adaptive weights. Caches reads to avoid I/O bottlenecks.
2.  **TrendAnalyzer (`services/trendAnalyzer.ts`):** Extracts top keywords excluding stop words, identifies >50% category spikes, and detects geographic clustering by rounding coordinates (~1.1km).
3.  **AdaptiveWeights (`services/adaptiveWeights.ts`):** Adjusts category severity weights (capped at 10) and tunes the duplicate detection threshold based on issue volume. Saves state to `data/modelWeights.json`.
4.  **IntelligenceIndex (`services/intelligenceIndex.ts`):** Generates daily Civic Intelligence JSON snapshots in `data/dailySnapshots/`, calculating an index score that rewards resolution and penalizes category spikes.
5.  **DailyRefinementJob (`scheduler/dailyRefinementJob.ts`):** The orchestrator scheduled via `node-cron` that runs the daily cycle.

## Daily Cycle Algorithm
Every day at 00:00, the scheduled job runs the following steps:

### 1. Trend Detection
-   Fetches issues submitted in the last 24 hours from the local SQLite database.
-   **Keyword Extraction:** Identifies top 5 most common keywords by extracting words >= 3 characters and filtering common stop words.
-   **Category Spikes:** Compares the current day's category volume with the previous 24 hours. A spike is flagged if the volume is > 5 and there is a ≥ 50% increase.
-   **Geographic Clustering:** Rounds latitude and longitude to 2 decimal places to cluster issues and find the highest severity region.

### 2. Adaptive Weight Optimization
The system learns from platform activity:
-   **Logic:** It tracks issues that are assigned or resolved. If a category receives > 5 critical resolutions, its severity weight multiplier is increased by 0.5 (capped at 10).
-   **Goal:** Automatically classify similar future issues as higher severity, reducing manual intervention.

### 3. Duplicate Detection Threshold Adjustment
-   **Logic:** Adjusts the global duplicate threshold based on overall volume.
    -   If volume > 100: Tightens the threshold (+0.01, max 0.95).
    -   If volume < 20: Relaxes the threshold (-0.01, min 0.70).

### 4. Civic Intelligence Index
A daily score (0-100) reflecting platform activity and issue resolution.
-   **Base Score:** Starts at 50.0.
-   **Bonus:** Boosted by the ratio of resolved issues. Small reward for rich keyword descriptions.
-   **Penalty:** Penalized by the number of sudden category spikes (-1.5 per spike).

## Data Storage & Auditability
-   **Model Weights:** Stored locally in `data/modelWeights.json`. The `AdaptiveWeights` service preserves a 30-day history of previous weights to ensure full auditability of the model's evolution.
-   **Daily Snapshots:** Saved in `data/dailySnapshots/YYYY-MM-DD.json`. Contains the index score, delta, emerging concerns, and the highest severity region.

## Evolution Logic
The system evolves continuously. If "Pothole" issues are frequently marked as resolved/critical, the model learns that "Pothole" is more critical and automatically boosts its severity score via `PriorityEngine`. The duplicate threshold dynamically breathes (tightens or relaxes) based on the overall activity density, ensuring the platform remains highly adaptive to real-world infrastructure problems.