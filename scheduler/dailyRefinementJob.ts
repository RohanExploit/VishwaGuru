import cron from 'node-cron';
import fs from 'fs';
import path from 'path';

import { TrendAnalyzer } from '../services/trendAnalyzer';
import { PriorityEngine } from '../services/priorityEngine';
import { AdaptiveWeights } from '../services/adaptiveWeights';
import { IntelligenceIndex } from '../services/intelligenceIndex';

export class DailyRefinementJob {
    private dbPath: string;
    private snapshotDir: string;
    private weightsFile: string;

    constructor(
        dbPath: string = './data/issues.db',
        snapshotDir: string = './data/dailySnapshots',
        weightsFile: string = './data/modelWeights.json'
    ) {
        this.dbPath = dbPath;
        this.snapshotDir = snapshotDir;
        this.weightsFile = weightsFile;
    }

    public async runCycle(): Promise<void> {
        console.log(`[${new Date().toISOString()}] Starting Daily Civic Intelligence Refinement...`);

        try {
            // Initialize services
            const trendAnalyzer = new TrendAnalyzer(this.dbPath, this.snapshotDir);
            const priorityEngine = new PriorityEngine(this.dbPath);
            const adaptiveWeights = new AdaptiveWeights(this.weightsFile);
            const intelligenceIndex = new IntelligenceIndex(this.dbPath);

            // 1. Trend Analysis
            const { issues, trends } = await trendAnalyzer.analyze();
            console.log(`Analyzed ${issues.length} issues from the last 24 hours.`);

            // 2. Adaptive Weight Optimization
            const weightUpdates = await priorityEngine.autoAdjustSeverity();
            const categoryChanges = adaptiveWeights.updateCategoryWeights(weightUpdates);

            // 3. Duplicate Pattern Learning
            const radiusChange = adaptiveWeights.updateDuplicateRadius(trends.clusters.length, issues.length);

            const allWeightChanges = [...categoryChanges];
            if (radiusChange) allWeightChanges.push(radiusChange);

            // 4. Civic Intelligence Index
            const indexData = await intelligenceIndex.generateDailyScore(trends);

            // Print snapshot summary
            let scoreDiffText = "";
            // Optional: load previous score to calculate diff
            const previousScore = this.getPreviousScore();
            if (previousScore !== null) {
                const diff = (indexData.score - previousScore).toFixed(1);
                scoreDiffText = `(${Number(diff) > 0 ? '+' : ''}${diff} from yesterday)`;
            }

            console.log(`Civic Intelligence Index: ${indexData.score} ${scoreDiffText}`);
            console.log(`Top Emerging Concern: ${indexData.top_emerging_concern}`);
            console.log(`Highest Severity Region: ${indexData.highest_severity_region}`);

            // 5. Store Snapshot JSON
            const snapshot = {
                date: new Date().toISOString(),
                trends: trends,
                civic_index: indexData,
                weight_updates: weightUpdates,
                weight_changes: allWeightChanges,
                model_weights: adaptiveWeights.getWeights()
            };

            const filename = `${new Date().toISOString().split('T')[0]}.json`;
            const filepath = path.join(this.snapshotDir, filename);

            if (!fs.existsSync(this.snapshotDir)) {
                fs.mkdirSync(this.snapshotDir, { recursive: true });
            }

            fs.writeFileSync(filepath, JSON.stringify(snapshot, null, 2));
            console.log(`Daily snapshot saved to ${filepath}`);

        } catch (error) {
            console.error("Error in daily refinement cycle:", error);
        }
    }

    private getPreviousScore(): number | null {
        try {
            if (!fs.existsSync(this.snapshotDir)) return null;
            const files = fs.readdirSync(this.snapshotDir).filter(f => f.endsWith('.json')).sort();
            if (files.length === 0) return null;
            const latest = files[files.length - 1];
            const data = JSON.parse(fs.readFileSync(path.join(this.snapshotDir, latest), 'utf-8'));
            return data.civic_index?.score || null;
        } catch (e) {
            return null;
        }
    }

    public startSchedule() {
        console.log("Scheduling daily refinement job (00:00 UTC)...");
        // Run daily at midnight
        cron.schedule('0 0 * * *', async () => {
            await this.runCycle();
        });
    }
}

// Entry point when run directly
if (require.main === module) {
    const job = new DailyRefinementJob();
    job.startSchedule();
}
