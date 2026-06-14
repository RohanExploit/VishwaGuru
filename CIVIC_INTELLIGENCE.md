# Daily Civic Intelligence Refinement Engine

## Overview
VishwaGuru's Civic Intelligence Engine is a self-improving AI system that runs daily at midnight to analyze civic issues, detect trends, and optimize the system's severity scoring logic based on real-world patterns.

## Architecture

The engine is composed of the following modules:
1.  **TrendAnalyzer (`backend/trend_analyzer.py`):** Extracts top keywords and identifies geographic clusters using DBSCAN.
2.  **AdaptiveWeights (`backend/adaptive_weights.py`):** Manages dynamic severity scoring weights stored in `backend/data/modelWeights.json`.
3.  **CivicIntelligenceEngine (`backend/civic_intelligence.py`):** The orchestrator that runs the daily cycle.

## Daily Cycle Algorithm

Every day at 00:00 UTC, the system performs the following steps:

### 1. Trend Detection
*   Analyzes all issues submitted in the last 24 hours.
*   **Keyword Extraction:** Identifies top 5 most common keywords (excluding stop words).
*   **Category Spikes:** Compares current category volume with the previous day's snapshot. A category is flagged as a "spike" if:
    *   Volume > 5
    *   Increase > 50% compared to yesterday.
*   **Geographic Clustering:** Uses DBSCAN (Density-Based Spatial Clustering of Applications with Noise) to find clusters of issues (e.g., multiple reports of the same pothole).

### 2. Adaptive Weight Optimization
The system learns from manual interventions:
*   **Input:** Queries `EscalationAudit` logs for "Severity Upgrades" (manual overrides where an admin increased the severity).
*   **Logic:** If a category receives ≥ 3 manual upgrades in 24 hours, its severity multiplier is increased by 10% (x1.1).
*   **Goal:** To automatically classify similar future issues as higher severity, reducing the need for manual intervention.

### 3. Duplicate Pattern Learning
*   **Input:** Geographic clustering density.
*   **Logic:**
    *   If many clusters (>5) are found: Increase duplicate search radius (x1.05) to better group reports.
    *   If volume is high (>50) but no clusters: Increase radius (x1.05) as the current radius might be too strict.
    *   If volume is low (<10) and radius is large: Decay radius (x0.95) to improve precision.

### 4. Civic Intelligence Index
A daily score (0-100) reflecting the city's civic health.
*   **Base Score:** 70
*   **Bonus:** +2.0 per resolved issue.
*   **Penalty:** -0.5 per new issue.
*   **Output:** Includes "Top Emerging Concern" and "Highest Severity Region".

## Data Storage & Auditability

### Model Weights
*   Dynamic weights are stored in `backend/data/modelWeights.json`.
*   This file is hot-reloaded by the application without restart.

### Daily Snapshots
*   Stored in `backend/data/dailySnapshots/YYYY-MM-DD.json`.
*   Contains:
    *   `civic_index`: The calculated score and metrics.
    *   `trends`: Keywords, distribution, clusters, and detected spikes.
    *   `weight_changes`: A detailed audit log of what weights were changed, the old value, the new value, and the reason.
    *   `model_weights`: A copy of the full weight configuration at the time of the snapshot for full reproducibility.

## Evolution Logic
The system evolves by:
1.  **Self-Correction:** If admins constantly upgrade "Pothole" severity, the system learns that "Pothole" is more critical than initially configured.
2.  **Dynamic Sensitivity:** The duplicate detection radius "breathes" (expands/contracts) based on the density of reports, adapting to urban density changes or event-driven spikes.
