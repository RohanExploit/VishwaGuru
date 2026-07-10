import cron from 'node-cron';
import fs from 'fs';
import path from 'path';
import { TrendAnalyzer } from '../services/trendAnalyzer';
import { AdaptiveWeights } from '../services/adaptiveWeights';
import { PriorityEngine } from '../services/priorityEngine';
import { IntelligenceIndex } from '../services/intelligenceIndex';

export async function runDailyRefinement() {
  console.log(`[${new Date().toISOString()}] Starting Daily Civic Intelligence Refinement...`);

  const analyzer = new TrendAnalyzer();
  const adapter = new AdaptiveWeights();
  const priority = new PriorityEngine();
  const indexer = new IntelligenceIndex();

  try {
    // 1. Trend Detection
    const { topKeywords, categorySpikes, locations, totalIssues } = await analyzer.analyzeLast24Hours();

    // 2. Adaptive Weight Optimization
    const updatedWeights = adapter.optimizeWeights(categorySpikes, totalIssues);

    // 3. Duplicate Threshold Adjustment
    const duplicateThreshold = priority.adjustDuplicateThreshold(totalIssues);

    // 4. Civic Intelligence Index
    const intel = indexer.calculateDailyIndex(totalIssues, topKeywords, categorySpikes, locations);

    // Generate Snapshot
    const today = new Date().toISOString().split('T')[0];
    const snapshotPath = path.resolve(process.cwd(), `data/dailySnapshots/${today}.json`);

    const snapshot = {
      date: today,
      metrics: {
        totalIssuesLast24h: totalIssues,
        topKeywords,
        categorySpikes
      },
      intelligenceIndex: {
        score: intel.index,
        diff: (intel.diff >= 0 ? '+' : '') + intel.diff,
        topEmergingConcern: intel.topConcern,
        highestSeverityRegion: intel.highestSeverityRegion
      },
      systemAdjustments: {
        duplicateDetectionThreshold: duplicateThreshold,
        severityWeights: updatedWeights
      }
    };

    const dir = path.dirname(snapshotPath);
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });

    fs.writeFileSync(snapshotPath, JSON.stringify(snapshot, null, 2));

    console.log(`Civic Intelligence Index: ${intel.index} (${snapshot.intelligenceIndex.diff} from yesterday)`);
    console.log(`Top Emerging Concern: ${intel.topConcern}`);
    console.log(`Highest Severity Region: ${intel.highestSeverityRegion}`);
    console.log(`Daily snapshot saved to ${snapshotPath}`);

  } catch (error) {
    console.error('Error during daily refinement:', error);
  } finally {
    analyzer.close();
  }
}

// Check for run-now flag
if (process.argv.includes('--run-now')) {
  runDailyRefinement().then(() => {
    console.log('Immediate execution completed.');
    process.exit(0);
  });
} else {
  // Schedule to run at 00:00 every day
  cron.schedule('0 0 * * *', () => {
    runDailyRefinement();
  });
  console.log('Daily Refinement Engine scheduled for 00:00 daily.');
}
