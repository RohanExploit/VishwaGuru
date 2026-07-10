# Civic Intelligence Refinement Engine

The Civic Intelligence Refinement Engine is a self-improving infrastructure component that runs locally every day at 00:00. It processes all civic issues submitted in the last 24 hours to automatically optimize the system's analytical capabilities without requiring external APIs.

## Architecture

The engine is composed of four main local services orchestrated by a `node-cron` scheduled job.

### 1. Trend Analyzer (`services/trendAnalyzer.ts`)
- **Purpose:** Identifies new patterns and trending topics.
- **Algorithm:**
  - Extracts and counts words from issue descriptions, filtering out common stopwords.
  - Determines the top 5 most common keywords used in the last 24 hours.
  - Compares the volume of issues per category in the last 24 hours against the 7-day historical average. A ratio > 1.5 indicates a category spike.

### 2. Adaptive Weights (`services/adaptiveWeights.ts`)
- **Purpose:** Refines severity scoring weights dynamically based on user engagement.
- **Algorithm:**
  - Analyzes the ratio of total upvotes to the total issue count per category in the last 24 hours.
  - If a category receives high user engagement (e.g., upvote ratio > 10), its severity weight is incremented.
  - If a category loses engagement, its weight gradually decays back to baseline.
  - Maintains an `audit_history` in `data/modelWeights.json` to ensure transparency and track parameter evolution.

### 3. Priority Engine (`services/priorityEngine.ts`)
- **Purpose:** Adjusts duplicate detection sensitivity dynamically.
- **Algorithm:**
  - Monitors the total volume of submitted issues over 24 hours.
  - In high-volume scenarios (e.g., > 1000 issues), the similarity threshold is lowered, grouping more issues together to prevent system flooding.
  - In low-volume scenarios, the threshold is raised to ensure strict, highly accurate duplicate detection.
  - Threshold adjustments are logged to the `audit_history`.

### 4. Intelligence Index (`services/intelligenceIndex.ts`)
- **Purpose:** Generates a daily health and activity score for the civic environment.
- **Algorithm:**
  - Calculates a base score of 50.
  - Adds up to 30 points based on the ratio of resolved to total issues in the last 24 hours.
  - Identifies the highest severity region by aggregating upvotes based on location.
  - Extracts the top emerging concern from the detected category spikes or keywords.
  - Saves the resulting summary as a JSON snapshot in `data/dailySnapshots/YYYY-MM-DD.json`.

## Data Storage
The system operates entirely on local databases and files:
- **`backend/data/issues.db`**: Source of truth for issues, accessed in read-only mode by the engine.
- **`data/modelWeights.json`**: Persists the adaptive severity weights, duplicate thresholds, and algorithmic audit logs.
- **`data/dailySnapshots/`**: Archives the historical daily Civic Intelligence Index scores.

## Manual Trigger
To run the refinement job manually outside of its midnight schedule, use:
```bash
npx ts-node scheduler/dailyRefinementJob.ts --run-now
```
