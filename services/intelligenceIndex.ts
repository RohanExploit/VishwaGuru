import * as fs from 'fs';
import * as path from 'path';

export interface DailySnapshot {
    date: string;
    civicIntelligenceIndex: number;
    delta: number;
    topEmergingConcern: string | null;
    highestSeverityRegion: string | null;
    topKeywords: string[];
}

export class IntelligenceIndex {
    private snapshotsDir: string;

    constructor() {
        this.snapshotsDir = process.env.SNAPSHOTS_DIR || path.resolve(__dirname, '../data/dailySnapshots');
        if (!fs.existsSync(this.snapshotsDir)) {
            fs.mkdirSync(this.snapshotsDir, { recursive: true });
        }
    }

    calculateIndexScore(categorySpikes: Record<string, number>, topKeywordsCount: number): number {
        // Base score: 50
        // More spikes = lower intelligence (system overwhelmed)
        // Less spikes / more resolved = higher intelligence

        let score = 50.0;
        let spikePenalty = 0;

        for (const spikeValue of Object.values(categorySpikes)) {
            spikePenalty += (spikeValue / 100) * 2; // E.g., 50% spike -> -1, 200% spike -> -4
        }

        score -= Math.min(20, spikePenalty);

        // Add minimal reward for maintaining low active spikes
        if (spikePenalty === 0 && topKeywordsCount > 0) {
            score += 2;
        }

        // Cap score
        return Math.max(0, Math.min(100, Number(score.toFixed(1))));
    }

    generateSnapshot(
        categorySpikes: Record<string, number>,
        topKeywords: string[],
        highestSeverityRegion: string | null
    ): DailySnapshot {
        const today = new Date().toISOString().split('T')[0]; // YYYY-MM-DD

        let topEmergingConcern: string | null = null;
        let maxSpike = 0;
        for (const [category, spike] of Object.entries(categorySpikes)) {
            if (spike > maxSpike) {
                maxSpike = spike;
                topEmergingConcern = category;
            }
        }

        const score = this.calculateIndexScore(categorySpikes, topKeywords.length);

        // Find yesterday's snapshot to calculate delta
        const yesterday = new Date();
        yesterday.setDate(yesterday.getDate() - 1);
        const yesterdayFile = path.join(this.snapshotsDir, `${yesterday.toISOString().split('T')[0]}.json`);

        let delta = 0;
        if (fs.existsSync(yesterdayFile)) {
            try {
                const pastData: DailySnapshot = JSON.parse(fs.readFileSync(yesterdayFile, 'utf8'));
                delta = Number((score - pastData.civicIntelligenceIndex).toFixed(1));
            } catch (err) {
                console.error("Failed to parse yesterday's snapshot", err);
            }
        } else {
            // First time running, just default to positive base
            delta = Number((score - 50.0).toFixed(1));
        }

        const snapshot: DailySnapshot = {
            date: today,
            civicIntelligenceIndex: score,
            delta,
            topEmergingConcern,
            highestSeverityRegion,
            topKeywords
        };

        return snapshot;
    }

    saveSnapshot(snapshot: DailySnapshot) {
        const filePath = path.join(this.snapshotsDir, `${snapshot.date}.json`);
        fs.writeFileSync(filePath, JSON.stringify(snapshot, null, 2));
    }
}
