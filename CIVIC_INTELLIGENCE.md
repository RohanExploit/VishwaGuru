# 🧠 Daily Civic Intelligence Refinement Engine

The Daily Civic Intelligence Refinement Engine is an autonomous, self-improving infrastructure layer of VishwaGuru. It is a standalone TypeScript process scheduled to run daily at 00:00.

## 🚀 Purpose

VishwaGuru is designed to continuously evolve without human intervention. By analyzing the civic issues reported by users every day, the platform intelligently adjusts its own behavior, prioritizing emerging problems and adapting spatial clustering tolerances.

## 🏗️ Components

The architecture relies on fully local Node.js services reading directly from the `issues` database and storing logic in local JSON files to avoid API overhead.

1. **`trendAnalyzer`**: Parses the last 24h and 48h of civic data.
    - **Keyword Extraction**: Identifies the top 5 emerging words from issue descriptions.
    - **Category Spikes**: Detects if a category's volume increased by >50% compared to the previous day.
    - **Geographic Clustering**: Identifies spatial clusters (e.g., localized flooding) to track high-severity regions.

2. **`adaptiveWeights`**: Dynamically adjusts system parameters based on the `trendAnalyzer`.
    - Automatically increases the severity weight of categories experiencing spikes, meaning subsequent incoming reports of that type will be flagged as higher urgency.
    - Automatically adjusts the duplicate detection proximity threshold depending on the density of the highest-severity region.
    - Maintains an auditable history of previous weights in `modelWeights.json`.

3. **`intelligenceIndex`**: Calculates a daily "Civic Intelligence Index" score.
    - Ranges up to 100. Points are deducted based on system strain (unresolved spikes) and rewarded for consistent activity.
    - Generates and stores a historical `snapshot.json` to map VishwaGuru's daily operational efficiency.

4. **`priorityEngine` & `dailyRefinementJob`**: The orchestrator and cron schedule.
    - Operates completely offline without the use of external cloud APIs or complex message brokers.

## 📂 Architecture

- `/services/`: Core logic (analyzing, adapting, indexing).
- `/scheduler/`: Execution trigger (`node-cron`).
- `/data/modelWeights.json`: Auditable adaptive parameter registry.
- `/data/dailySnapshots/`: JSON files mapping daily intelligence scores.

## 🛠️ Testing

Run tests to ensure system integrity:
```bash
npm test
```
