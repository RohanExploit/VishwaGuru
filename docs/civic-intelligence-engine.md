# Daily Civic Intelligence Refinement Engine

## Overview
The Daily Civic Intelligence Refinement Engine is a scheduled job that acts as a self-improving AI infrastructure for VishwaGuru. It analyzes civic issues submitted in the last 24 hours to automatically optimize system parameters locally without external dependencies.

It runs every day at 00:00 using a pure local SQLite database and saves daily analytics snapshots as JSON files.

## Algorithm and Evolution Logic

The Refinement Engine consists of four core modular services:

### 1. TrendAnalyzer (`services/trendAnalyzer.ts`)
*   **Logic:** Connects to `backend/data/issues.db` to extract all issues from the past 24 hours.
*   **Evolution:** Identifies the top 5 emerging keywords using basic tokenization and stop-word removal. Tracks category volume spikes and groups incidents by geographic region (ward/location) to provide early warning of mass issues (like localized water outages).

### 2. AdaptiveWeights (`services/adaptiveWeights.ts`)
*   **Logic:** Adjusts severity scoring weights dynamically based on historical category submission volumes.
*   **Evolution:** If a specific category represents more than 10% of the daily issue volume, the engine identifies it as a critical priority and automatically bumps its severity multiplier weight by `+0.1`.
*   **Auditability:** A complete history of past daily weights is appended and preserved inside `data/modelWeights.json`.

### 3. PriorityEngine (`services/priorityEngine.ts`)
*   **Logic:** Modifies the baseline similarity detection threshold used to cluster mass-reported duplicates.
*   **Evolution:** If daily submissions spike abnormally (e.g. >1000 issues/day), the duplicate matching threshold loosens from `0.85` (85% similarity) down to `0.70`. This groups similar complaints faster to deal with mass-reporting events without overwhelming the triaging officers.

### 4. IntelligenceIndex (`services/intelligenceIndex.ts`)
*   **Logic:** Computes a daily Civic Intelligence Index baseline metric assessing the overall state of the city.
*   **Evolution:** Start from a baseline score of 50.0. Heavy localized issue concentration negatively impacts the index. The system diffs today's score against yesterday's to measure day-over-day civic performance (+X.X or -X.X). Results generate a daily snapshot stored in `data/dailySnapshots/YYYY-MM-DD.json`.
