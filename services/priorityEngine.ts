import { TrendAnalyzer } from './trendAnalyzer';
import { AdaptiveWeights } from './adaptiveWeights';
import { IntelligenceIndex, DailySnapshot } from './intelligenceIndex';

export class PriorityEngine {
    private trendAnalyzer: TrendAnalyzer;
    private adaptiveWeights: AdaptiveWeights;
    private intelligenceIndex: IntelligenceIndex;

    constructor() {
        this.trendAnalyzer = new TrendAnalyzer();
        this.adaptiveWeights = new AdaptiveWeights();
        this.intelligenceIndex = new IntelligenceIndex();
    }

    async runDailyRefinement(): Promise<DailySnapshot> {
        console.log(`[${new Date().toISOString()}] Starting Daily Civic Intelligence Refinement...`);

        // Step 1: Trend Detection
        console.log(`[${new Date().toISOString()}] Step 1: Trend Detection`);
        const { topKeywords, categorySpikes, highestSeverityRegion } = await this.trendAnalyzer.analyzeLast24h();

        console.log(`Top Keywords: ${topKeywords.join(', ') || 'None'}`);
        console.log(`Spikes Detected: ${Object.keys(categorySpikes).length}`);
        if (highestSeverityRegion) {
            console.log(`Highest Severity Region Detected at: ${highestSeverityRegion}`);
        }

        // Step 2: Adaptive Weight Optimization
        console.log(`[${new Date().toISOString()}] Step 2: Adaptive Weight Optimization`);
        const updatedWeights = this.adaptiveWeights.adjustWeights(categorySpikes, highestSeverityRegion);
        console.log(`Duplicate threshold adjusted to: ${updatedWeights.duplicateThreshold}`);

        // Step 3: Civic Intelligence Index
        console.log(`[${new Date().toISOString()}] Step 3: Generating Civic Intelligence Index`);
        const snapshot = this.intelligenceIndex.generateSnapshot(
            categorySpikes,
            topKeywords,
            highestSeverityRegion
        );

        // Save daily metadata snapshot
        this.intelligenceIndex.saveSnapshot(snapshot);
        console.log(`[${new Date().toISOString()}] Daily Refinement Complete.`);
        console.log(`Summary: Index: ${snapshot.civicIntelligenceIndex} (${snapshot.delta >= 0 ? '+' : ''}${snapshot.delta})`);

        return snapshot;
    }
}
