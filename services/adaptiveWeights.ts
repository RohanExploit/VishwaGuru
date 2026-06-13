import { Issue, ModelWeights } from "./types";
import * as fs from "fs";
import * as path from "path";

export class AdaptiveWeights {
  private configPath: string;

  constructor(
    configPath: string = path.join(__dirname, "../data/modelWeights.json"),
  ) {
    this.configPath = configPath;
  }

  public loadWeights(): ModelWeights {
    if (fs.existsSync(this.configPath)) {
      const data = fs.readFileSync(this.configPath, "utf-8");
      return JSON.parse(data);
    }

    // Default weights
    return {
      categoryWeights: {
        Pothole: 5,
        Garbage: 3,
        "Water Supply": 4,
        Streetlight: 2,
        Flooding: 8,
      },
      duplicateThreshold: 0.85,
      lastUpdated: new Date().toISOString(),
      history: [],
    };
  }

  public optimizeWeights(
    issues: Issue[],
    currentWeights: ModelWeights,
  ): ModelWeights {
    const newWeights = JSON.parse(
      JSON.stringify(currentWeights),
    ) as ModelWeights;

    // Adjust category severity based on volume and resolutions
    const categoryCounts: Record<string, number> = {};
    const criticalResolutions: Record<string, number> = {};

    issues.forEach((issue) => {
      categoryCounts[issue.category] =
        (categoryCounts[issue.category] || 0) + 1;
      // If it was assigned or resolved, we might treat it as critical
      if (issue.status === "resolved" || issue.assigned_to) {
        criticalResolutions[issue.category] =
          (criticalResolutions[issue.category] || 0) + 1;
      }
    });

    for (const [category, count] of Object.entries(criticalResolutions)) {
      if (count > 5) {
        // Threshold to increase weight
        const increase = 0.5; // Bump weight by 0.5
        const currentWeight = newWeights.categoryWeights[category] || 1;
        newWeights.categoryWeights[category] = Math.min(
          10,
          currentWeight + increase,
        ); // Cap at 10
      }
    }

    // Dynamic duplicate threshold based on clustering density
    // If we have high volume overall, tighten the duplicate threshold
    if (issues.length > 100) {
      newWeights.duplicateThreshold = Math.min(
        0.95,
        newWeights.duplicateThreshold + 0.01,
      );
    } else if (issues.length < 20) {
      newWeights.duplicateThreshold = Math.max(
        0.7,
        newWeights.duplicateThreshold - 0.01,
      );
    }

    // Store history
    newWeights.history.push({
      date: new Date().toISOString().split("T")[0],
      categoryWeights: currentWeights.categoryWeights,
      duplicateThreshold: currentWeights.duplicateThreshold,
    });

    // Keep only last 30 days of history
    if (newWeights.history.length > 30) {
      newWeights.history.shift();
    }

    newWeights.lastUpdated = new Date().toISOString();
    return newWeights;
  }

  public saveWeights(weights: ModelWeights): void {
    fs.writeFileSync(
      this.configPath,
      JSON.stringify(weights, null, 2),
      "utf-8",
    );
  }
}
