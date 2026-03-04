import * as sqlite3 from 'sqlite3';

export interface TrendAnalysisResult {
    topKeywords: string[];
    categorySpikes: Record<string, number>;
    highestSeverityRegion: string | null;
}

const STOP_WORDS = new Set([
    'the', 'is', 'in', 'at', 'of', 'on', 'and', 'a', 'to', 'for', 'with', 'as', 'by', 'an', 'this', 'that', 'it', 'are', 'be', 'or', 'from', 'but', 'not'
]);

export class TrendAnalyzer {

    async analyzeLast24h(): Promise<TrendAnalysisResult> {
        const dbPath = process.env.DB_PATH || './data/issues.db';
        const db = new sqlite3.Database(dbPath);

        const allAsync = (query: string, params: any[]): Promise<any[]> => {
            return new Promise((resolve, reject) => {
                db.all(query, params, (err, rows) => {
                    if (err) reject(err);
                    else resolve(rows);
                });
            });
        };

        const now = new Date();
        const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000);
        const twoDaysAgo = new Date(now.getTime() - 48 * 60 * 60 * 1000);

        try {
            const issues24h = await allAsync(
                `SELECT description, category, latitude, longitude FROM issues WHERE created_at >= ?`,
                [yesterday.toISOString()]
            );

            const issues48hTo24h = await allAsync(
                `SELECT category FROM issues WHERE created_at >= ? AND created_at < ?`,
                [twoDaysAgo.toISOString(), yesterday.toISOString()]
            );

            const topKeywords = this.extractTopKeywords(issues24h.map(i => i.description).filter(d => d));
            const categorySpikes = this.detectCategorySpikes(issues24h, issues48hTo24h);
            const highestSeverityRegion = this.detectGeographicClustering(issues24h);

            return { topKeywords, categorySpikes, highestSeverityRegion };
        } finally {
            db.close();
        }
    }

    extractTopKeywords(descriptions: string[]): string[] {
        const wordCounts: Record<string, number> = {};

        for (const desc of descriptions) {
            const words = desc.toLowerCase().match(/\b\w+\b/g) || [];
            for (const word of words) {
                if (word.length > 3 && !STOP_WORDS.has(word)) {
                    wordCounts[word] = (wordCounts[word] || 0) + 1;
                }
            }
        }

        return Object.entries(wordCounts)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 5)
            .map(entry => entry[0]);
    }

    detectCategorySpikes(recentIssues: any[], olderIssues: any[]): Record<string, number> {
        const recentCounts: Record<string, number> = {};
        const olderCounts: Record<string, number> = {};

        for (const issue of recentIssues) {
            if (issue.category) recentCounts[issue.category] = (recentCounts[issue.category] || 0) + 1;
        }
        for (const issue of olderIssues) {
            if (issue.category) olderCounts[issue.category] = (olderCounts[issue.category] || 0) + 1;
        }

        const spikes: Record<string, number> = {};
        for (const category in recentCounts) {
            const newFreq = recentCounts[category];
            const oldFreq = olderCounts[category] || 0;

            if (oldFreq > 0) {
                const increase = ((newFreq - oldFreq) / oldFreq) * 100;
                if (increase >= 50) spikes[category] = increase; // >50% spike
            } else if (newFreq >= 3) {
                spikes[category] = 100; // New category with sufficient occurrences
            }
        }

        return spikes;
    }

    detectGeographicClustering(issues: any[]): string | null {
        const regionCounts: Record<string, number> = {};

        for (const issue of issues) {
            if (issue.latitude != null && issue.longitude != null) {
                const latRounded = issue.latitude.toFixed(2);
                const lonRounded = issue.longitude.toFixed(2);
                const region = `${latRounded},${lonRounded}`;
                regionCounts[region] = (regionCounts[region] || 0) + 1;
            }
        }

        let highestRegion: string | null = null;
        let maxCount = 0;

        for (const [region, count] of Object.entries(regionCounts)) {
            if (count > maxCount && count >= 3) {
                maxCount = count;
                highestRegion = region;
            }
        }

        return highestRegion;
    }
}
