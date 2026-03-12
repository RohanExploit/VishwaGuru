import { Issue, DailySnapshot } from "./types";
import * as fs from "fs";
import * as path from "path";

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

    // Also save a human-readable markdown report
    this.saveMarkdownReport(snapshot);
  }

  private saveMarkdownReport(snapshot: DailySnapshot): void {
    const filePath = path.join(this.snapshotsDir, `REPORT_${snapshot.date}.md`);
    let markdown = `# Daily Civic Intelligence Report: ${snapshot.date}\n\n`;
    markdown += `**Civic Intelligence Index**: ${snapshot.indexScore} (${snapshot.delta >= 0 ? '+' : ''}${snapshot.delta} from yesterday)\n\n`;

    markdown += `## Top 5 Emerging Keywords\n`;
    if (snapshot.topKeywords.length > 0) {
      snapshot.topKeywords.forEach((kw, i) => {
        markdown += `${i + 1}. ${kw}\n`;
      });
    } else {
      markdown += `*No significant keywords detected.*\n`;
    }

    markdown += `\n## Emerging Concerns (Spikes)\n`;
    if (snapshot.emergingConcerns.length > 0) {
      snapshot.emergingConcerns.forEach(concern => {
        markdown += `- **${concern.category}**: +${concern.increasePercentage}%\n`;
      });
    } else {
      markdown += `*No significant category spikes detected.*\n`;
    }

    markdown += `\n## Highest Severity Region\n`;
    if (snapshot.highestSeverityRegion) {
      markdown += `- Location: [${snapshot.highestSeverityRegion.latitude}, ${snapshot.highestSeverityRegion.longitude}]\n`;
      markdown += `- Issue Count: ${snapshot.highestSeverityRegion.count}\n`;
    } else {
      markdown += `*No significant regional clustering detected.*\n`;
    }

    fs.writeFileSync(filePath, markdown, "utf-8");
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
