# Daily Civic Intelligence Refinement Engine (TypeScript)

This documentation outlines the architecture, algorithms, and evolution logic of the **TypeScript implementation** of the Daily Civic Intelligence Refinement Engine.

## Objective

The engine transforms the platform into a self-improving AI infrastructure. Every day at midnight, it analyzes all submitted civic issues from the previous 24 hours, detects new patterns, refines severity scoring weights dynamically, improves duplicate detection parameters, and generates a "Civic Intelligence Index".

## System Architecture

The TypeScript module is built entirely with local database dependencies (SQLite) without calling any external APIs. It is structured into multiple decoupled services.

### 1. `services/trendAnalyzer.ts`
- **Purpose**: Detects emerging civic patterns.
- **Process**:
  - Extracts the top 5 most common keywords from issue descriptions (filtering out stop words).
  - Calculates the distribution of issue categories over the last 24h.
  - Detects **Category Spikes** by comparing current volume against the previous day's snapshot (>50% increase).
  - Identifies **Geographic Clusters** using a simple Haversine proximity check (radius: 100m) grouping dense issues.

### 2. `services/priorityEngine.ts`
- **Purpose**: Scans for manual feedback to propose weight optimizations.
- **Process**:
  - Queries `escalation_audits` to count how many times an issue was marked as a `SEVERITY_UPGRADE` in the last 24 hours.
  - If a category is upgraded more than the threshold (e.g., 3 times), it proposes a 10% increase to that category's priority weight.

### 3. `services/adaptiveWeights.ts`
- **Purpose**: Safely updates and persists the AI system's learning weights.
- **Process**:
  - Reads from `data/modelWeights.json`.
  - Applies factor updates provided by the `priorityEngine` (clamping values between 0.5 and 3.0).
  - Dynamically updates the global duplicate search radius based on clustering density. If many clusters form, radius increases to group them. If volume drops, it slightly decays.
  - Appends old and new values to an `audit_history` array, preserving a fully auditable trail of model evolution.

### 4. `services/intelligenceIndex.ts`
- **Purpose**: Generates a composite score representing system health and civic activity.
- **Formula**:
  - Base Score: `70.0`
  - + `2.0` points for every resolved issue in the last 24h.
  - - `0.5` points for every newly reported issue.
  - Bound to `0-100`.
- Outputs top emerging concern (category with highest volume) and highest severity region (coordinates of the largest cluster).

### 5. `scheduler/dailyRefinementJob.ts`
- **Purpose**: Orchestrates the pipeline.
- **Process**:
  - Uses `node-cron` scheduled at `0 0 * * *` (midnight).
  - Calls `trendAnalyzer` -> `priorityEngine` -> `adaptiveWeights` -> `intelligenceIndex`.
  - Aggregates outputs and saves a JSON snapshot in `data/dailySnapshots/YYYY-MM-DD.json`.

## Data Persistence & Storage

- **Weights File (`data/modelWeights.json`)**: Contains category multipliers, severity keywords, dynamic thresholds, and the learning audit log.
- **Daily Snapshots (`data/dailySnapshots/*.json`)**: A historical record of system performance, trends, and daily deltas. These are loaded to calculate day-over-day changes like category spikes and index diffs.
