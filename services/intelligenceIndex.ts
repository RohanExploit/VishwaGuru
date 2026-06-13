import { Issue, DailySnapshot } from "./types";
import * as fs from "fs";
import * as path from "path";

/**
 * IntelligenceIndex: Produces a daily Civic Intelligence snapshot, aggregating
 * system performance metrics to capture overall municipal health and activity.
 *
 * Algorithm and Evolution Logic:
 * Starts at a 50.0 Index Baseline.
 * Increases (+): Base score raises by ratio of resolved civic issues (high resolutions = better performance).
 * Minor Bonus (+): If top keywords contain rich descriptions, minor bump (+0.5 per keyword).
 * Penalizes (-): Immediate penalty per significant Category Spikes (-1.5 per concern) to represent unmet issues.
 * Stores a JSON snapshot daily (e.g. data/dailySnapshots/YYYY-MM-DD.json) comparing delta changes.
 */
export class IntelligenceIndex {
  private snapshotsDir: string;

  constructor(
    snapshotsDir: string = path.join(__dirname, "../data/dailySnapshots"),
  ) {
    this.snapshotsDir = snapshotsDir;
    if (!fs.existsSync(this.snapshotsDir)) {
      fs.mkdirSync(this.snapshotsDir, { recursive: true });
    }
  }

  public generateIndex(
    issues: Issue[],
    topKeywords: string[],
    spikes: Array<{ category: string; increasePercentage: number }>,
    highestSeverityRegion?: {
      latitude: number;
      longitude: number;
      count: number;
    },
  ): DailySnapshot {
    let indexScore = 50.0; // Baseline

    // Logic for index calculation
    // - High number of resolved issues -> higher index
    // - High number of spikes -> lower index
    // - Reward system for keywords and clustering detection (active platform)

    const resolvedCount = issues.filter((i) => i.status === "resolved").length;
    const activeCount = issues.length - resolvedCount;

    // A higher resolution rate boosts the score, large spikes penalize it
    const resolutionRatio =
      issues.length > 0 ? (resolvedCount / issues.length) * 10 : 0;

    indexScore += resolutionRatio; // Boost for resolutions
    indexScore -= spikes.length * 1.5; // Penalty for sudden unhandled spikes
    indexScore += topKeywords.length * 0.5; // Small reward for rich descriptions

    // Normalize score to 0-100
    indexScore = Math.max(0, Math.min(100, indexScore));

    const todayDate = new Date().toISOString().split("T")[0];
    const previousScore = this.getPreviousIndexScore(todayDate);
    const delta = parseFloat((indexScore - previousScore).toFixed(1));

    const snapshot: DailySnapshot = {
      date: todayDate,
      indexScore: parseFloat(indexScore.toFixed(1)),
      delta,
      topKeywords,
      emergingConcerns: spikes.slice(0, 3), // Keep top 3 spikes as emerging concerns
      highestSeverityRegion,
    };

    return snapshot;
  }

  public saveSnapshot(snapshot: DailySnapshot): void {
    const filePath = path.join(this.snapshotsDir, `${snapshot.date}.json`);
    fs.writeFileSync(filePath, JSON.stringify(snapshot, null, 2), "utf-8");
  }

  private getPreviousIndexScore(todayDate: string): number {
    const files = fs
      .readdirSync(this.snapshotsDir)
      .filter((f) => f.endsWith(".json") && f !== `${todayDate}.json`)
      .sort((a, b) => b.localeCompare(a)); // Sort descending

    if (files.length > 0) {
      const prevData = fs.readFileSync(
        path.join(this.snapshotsDir, files[0]),
        "utf-8",
      );
      try {
        const parsed = JSON.parse(prevData) as DailySnapshot;
        return parsed.indexScore || 50.0;
      } catch (e) {
        return 50.0;
      }
    }
    return 50.0; // Default baseline if no previous day
  }
}
