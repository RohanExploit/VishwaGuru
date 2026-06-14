# 🧠 Daily Civic Intelligence Refinement Engine

The Daily Civic Intelligence Refinement Engine is an autonomous, self-improving infrastructure layer of VishwaGuru. It is a standalone TypeScript process scheduled to run daily at 00:00.

## 🚀 Purpose

VishwaGuru is designed to continuously evolve without human intervention. By analyzing the civic issues reported by users every day, the platform intelligently adjusts its own behavior, prioritizing emerging problems and adapting spatial clustering tolerances.

## 🏗️ Components

The architecture relies on fully local Node.js services reading directly from the `issues` database and storing logic in local JSON files to avoid API overhead.

### 1. Trend Detection
*   Analyzes all issues submitted in the last 24 hours.
*   **Keyword Extraction:** Identifies top 5 most common keywords (excluding stop words).
*   **Category Spikes:** Compares current category volume with the previous day's snapshot. A category is flagged as a "spike" if:
    *   Volume > 5
    *   Increase > 50% compared to yesterday.
*   **Geographic Clustering:** Uses DBSCAN (Density-Based Spatial Clustering of Applications with Noise) to find clusters of issues (e.g., multiple reports of the same pothole).
*   **Top Emerging Concern:** The system prioritizes the category with the highest percentage increase (spike) over raw volume. If no spikes are detected, the category with the highest volume is selected.

2. **`adaptiveWeights`**: Dynamically adjusts system parameters based on the `trendAnalyzer`.
    - Automatically increases the severity weight of categories experiencing spikes, meaning subsequent incoming reports of that type will be flagged as higher urgency.
    - Automatically adjusts the duplicate detection proximity threshold depending on the density of the highest-severity region.
    - Maintains an auditable history of previous weights in `modelWeights.json`.

3. **`intelligenceIndex`**: Calculates a daily "Civic Intelligence Index" score.
    - Ranges up to 100. Points are deducted based on system strain (unresolved spikes) and rewarded for consistent activity.
    - Generates and stores a historical `snapshot.json` to map VishwaGuru's daily operational efficiency.

### 4. Civic Intelligence Index
A daily score (0-100) reflecting the city's civic health.
*   **Base Score:** 70
*   **Bonus:** +2.0 per resolved issue.
*   **Penalty:** -0.5 per new issue.
*   **Delta Calculation:** Compares the current score with the previous day's score to show improvement or decline (e.g., `+3.1`).
*   **Output:** Includes "Top Emerging Concern", "Highest Severity Region", and the daily score change.

## 📂 Architecture

- `/services/`: Core logic (analyzing, adapting, indexing).
- `/scheduler/`: Execution trigger (`node-cron`).
- `/data/modelWeights.json`: Auditable adaptive parameter registry.
- `/data/dailySnapshots/`: JSON files mapping daily intelligence scores.

### Daily Snapshots
*   Stored in `backend/data/dailySnapshots/YYYY-MM-DD.json`.
*   Contains:
    *   `civic_index`: The calculated score, score delta, and metrics.
    *   `trends`: Keywords, distribution, clusters, and detected spikes.
    *   `weight_changes`: A detailed audit log of what weights were changed, the old value, the new value, and the reason.
    *   `model_weights`: A copy of the full weight configuration at the time of the snapshot for full reproducibility.

Run tests to ensure system integrity:
```bash
npm test
```
