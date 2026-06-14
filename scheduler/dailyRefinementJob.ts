import * as cron from "node-cron";
import * as sqlite3 from "sqlite3";
import * as path from "path";
import { TrendAnalyzer } from "../services/trendAnalyzer";
import { AdaptiveWeights } from "../services/adaptiveWeights";
import { IntelligenceIndex } from "../services/intelligenceIndex";
import { Issue } from "../services/types";

// Load environmental or fallback to test.db or production db
const dbPath =
  process.env.DB_PATH || path.join(__dirname, "../../backend/app.db");

export class DailyRefinementJob {
  private db: sqlite3.Database;
  private trendAnalyzer: TrendAnalyzer;
  private adaptiveWeights: AdaptiveWeights;
  private intelligenceIndex: IntelligenceIndex;

  constructor() {
    this.db = new sqlite3.Database(dbPath, (err) => {
      if (err) {
        console.error("Error connecting to local database:", err.message);
      } else {
        console.log(`Connected to local database at ${dbPath}`);
      }
    });
    this.trendAnalyzer = new TrendAnalyzer();
    this.adaptiveWeights = new AdaptiveWeights();
    this.intelligenceIndex = new IntelligenceIndex();
  }

  public async runRefinement() {
    console.log("--- Starting Daily Civic Intelligence Refinement ---");
    try {
      const issuesLast24h = await this.getIssues(24);
      const issuesPrev24h = await this.getIssues(48, 24);

      console.log(
        `Analyzing ${issuesLast24h.length} issues from the last 24 hours...`,
      );

      // 1. Trend Detection
      const topKeywords = this.trendAnalyzer.getTopKeywords(issuesLast24h, 5);
      const spikes = this.trendAnalyzer.detectCategorySpikes(
        issuesLast24h,
        issuesPrev24h,
      );
      const highestSeverityRegion =
        this.trendAnalyzer.identifyGeographicClustering(issuesLast24h);

      console.log(`Top 5 Emerging Keywords: ${topKeywords.join(", ")}`);

      // 2. Adaptive Weights Optimization
      const currentWeights = this.adaptiveWeights.loadWeights();
      const newWeights = this.adaptiveWeights.optimizeWeights(
        issuesLast24h,
        currentWeights,
      );
      this.adaptiveWeights.saveWeights(newWeights);
      console.log("Model weights optimized and updated for severity scoring.");

      // 3. Civic Intelligence Index Generation
      const snapshot = this.intelligenceIndex.generateIndex(
        issuesLast24h,
        topKeywords,
        spikes,
        highestSeverityRegion,
      );
      this.intelligenceIndex.saveSnapshot(snapshot);

      console.log("--- Refinement Complete ---");
      console.log(
        `Civic Intelligence Index: ${snapshot.indexScore} (${snapshot.delta >= 0 ? "+" : ""}${snapshot.delta} from yesterday)`,
      );
      if (snapshot.emergingConcerns.length > 0) {
        console.log(
          `Top Emerging Concern: ${snapshot.emergingConcerns[0].category} (+${snapshot.emergingConcerns[0].increasePercentage}%)`,
        );
      }
      if (snapshot.highestSeverityRegion) {
        console.log(
          `Highest Severity Region Center: [${snapshot.highestSeverityRegion.latitude}, ${snapshot.highestSeverityRegion.longitude}]`,
        );
      }
    } catch (error) {
      console.error("Error during daily refinement:", error);
    }
  }

  private getIssues(
    hoursEnd: number,
    hoursStart: number = 0,
  ): Promise<Issue[]> {
    return new Promise((resolve, reject) => {
      const query = `
        SELECT * FROM issues
        WHERE created_at >= datetime('now', '-${hoursEnd} hours')
        AND created_at <= datetime('now', '-${hoursStart} hours')
      `;

      this.db.all(query, [], (err, rows) => {
        if (err) {
          // If table doesn't exist, we just return empty array instead of failing
          if (err.message.includes("no such table")) {
            console.warn(
              "Table 'issues' does not exist yet. Returning empty issue list.",
            );
            return resolve([]);
          }
          reject(err);
        } else {
          resolve(rows as Issue[]);
        }
      });
    });
  }
}

// Ensure the process isn't immediately starting if imported by Jest
if (require.main === module) {
  const job = new DailyRefinementJob();

  // Run everyday at midnight
  cron.schedule("0 0 * * *", () => {
    job.runRefinement();
  });

  console.log(
    "Daily Civic Intelligence Refinement Engine scheduled at 00:00 every day.",
  );

  // For testing/manual trigger, we can also pass a flag or just run immediately if needed
  if (process.argv.includes("--run-now")) {
    job.runRefinement();
  }
}
