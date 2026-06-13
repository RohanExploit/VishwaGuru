# Priority Engine Algorithm Design

The VishwaGuru Issue Prioritization Engine is a modular, rule-based AI system designed to analyze civic complaints in real-time. It operates fully locally without external API dependencies, ensuring privacy, speed, and reliability.

## Core Components

The engine (`backend/priority_engine.py`) processes input text and optional image labels to determine three key metrics:

1.  **Severity Classification** (Critical, High, Medium, Low)
2.  **Urgency Score** (0-100)
3.  **Category Tagging** (Multi-label)

It also provides **Explainability** by returning the specific reasons (keywords or patterns) that triggered a high priority.

### 1. Severity Classification

Severity is determined by scanning the text for keywords mapped to four levels. The highest matched level determines the final severity.

-   **Critical (Score 90):** Life-threatening or major infrastructure failures.
    -   *Keywords:* fire, explosion, blood, death, collapse, gas leak, electric shock, flood, open manhole, live wire.
-   **High (Score 70):** Dangerous conditions, health hazards, or significant disruptions.
    -   *Keywords:* accident, injury, broken, hazard, sewage, disease, theft, traffic jam, pothole, dead animal.
-   **Medium (Score 40):** Nuisances, hygiene issues, or minor obstructions.
    -   *Keywords:* garbage, smell, noise, illegal parking, construction debris, graffiti.
-   **Low (Score 10):** Cosmetic issues or maintenance requests.
    -   *Keywords:* light flicker, faded sign, broken bench, aesthetic issues.

### 2. Urgency Scoring

The Urgency Score (0-100) starts with the Severity Score as a baseline and is modified by context:

-   **Base Score:** = Severity Score (e.g., Critical starts at 90).
-   **Temporal Modifiers:**
    -   "now", "immediately", "urgent": +20 points.
    -   "today", "tonight": +10 points.
    -   "yesterday", "last week": +5 points.
-   **Context Modifiers:**
    -   "fire", "smoke": +30 points.
    -   "blood", "injury": +25 points.
    -   "blocked", "stuck": +15 points.
    -   Sensitive locations (school, hospital): +15 points.
    -   Vulnerable groups (child, elderly): +10 points.

The final score is capped at 100.

### 3. Category Tagging

The engine detects categories by counting keyword matches for predefined categories such as:
-   Fire
-   Pothole
-   Street Light
-   Garbage
-   Water Leak
-   Stray Animal
-   Traffic Sign
-   ...and more.

The top 3 matching categories are returned.

## Explainability

Every analysis returns a `reasoning` list. This list contains human-readable strings explaining why a specific severity or urgency score was assigned (e.g., "Flagged as Critical due to keywords: fire, smoke").

## Performance Optimization

-   **Regex Compilation:** Key patterns are pre-compiled for speed.
-   **O(1) Lookups:** Keyword lists are optimized for fast checking.
-   **Local Execution:** No network latency or external API costs.

## Client-Side Mirror

A TypeScript implementation (`frontend/src/utils/priorityEngine.ts`) is provided to enable optimistic UI updates and immediate feedback to the user before the request even reaches the server.
