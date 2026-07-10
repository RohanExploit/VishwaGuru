import cron from 'node-cron';
import { TrendAnalyzer } from '../services/trendAnalyzer';
import { AdaptiveWeights } from '../services/adaptiveWeights';
import { PriorityEngine } from '../services/priorityEngine';
import { IntelligenceIndex } from '../services/intelligenceIndex';

export class DailyRefinementJob {
    public static async run(): Promise<void> {
        console.log(`[${new Date().toISOString()}] Starting Daily Civic Intelligence Refinement...`);

        try {
            // Target the last 24 hours
            const last24HoursStart = Date.now() - (24 * 60 * 60 * 1000);

            // 1. Trend Detection
            console.log('Running Trend Analyzer...');
            const trendAnalyzer = new TrendAnalyzer();
            const trends = trendAnalyzer.analyze(last24HoursStart);
            console.log(`Trends detected: ${trends.topKeywords.join(', ')}`);

            // 2. Adaptive Weight Optimization
            console.log('Running Adaptive Weights Optimizer...');
            const adaptiveWeights = new AdaptiveWeights();
            adaptiveWeights.optimize(last24HoursStart);

            // 3. Duplicate Pattern Learning
            console.log('Running Priority Engine...');
            const priorityEngine = new PriorityEngine();
            priorityEngine.adjustThresholds(last24HoursStart);

            // 4. Civic Intelligence Index Update
            console.log('Generating Intelligence Index Snapshot...');
            const intelligenceIndex = new IntelligenceIndex();
            const snapshot = intelligenceIndex.generateSnapshot(last24HoursStart, trends);

            console.log(`Refinement Complete. New Intelligence Index: ${snapshot.civicIntelligenceIndex}`);
        } catch (error) {
            console.error('Error during daily refinement:', error);
        }
    }

    public static startScheduler(): void {
        console.log('Initializing Daily Refinement Job Scheduler (Runs at 00:00 every day).');
        // Run at midnight every day
        cron.schedule('0 0 * * *', () => {
            this.run();
        });
    }
}

// Check for --run-now flag
if (require.main === module) {
    if (process.argv.includes('--run-now')) {
        DailyRefinementJob.run().then(() => {
            console.log('Manual run complete.');
            process.exit(0);
        });
    } else {
        DailyRefinementJob.startScheduler();
    }
}
