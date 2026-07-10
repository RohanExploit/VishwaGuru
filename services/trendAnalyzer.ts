import Database from 'better-sqlite3';
import path from 'path';

export interface TrendAnalysisResult {
    topKeywords: string[];
    categorySpikes: Record<string, { previousAvg: number; recent: number; spike: number }>;
}

export class TrendAnalyzer {
    private dbPath: string;

    constructor(dbPath: string = path.resolve(process.cwd(), 'backend/data/issues.db')) {
        this.dbPath = dbPath;
    }

    public analyze(last24HoursStart: number): TrendAnalysisResult {
        const db = new Database(this.dbPath, { readonly: true });

        try {
            // Get last 24h issues
            const stmt = db.prepare('SELECT description, category, created_at FROM issues WHERE created_at >= ?');

            // Format datetime as string since that is how it's stored in sqlite
            const dateStr = new Date(last24HoursStart).toISOString().replace('T', ' ').substring(0, 19);

            const recentIssues = stmt.all(dateStr) as any[];

            // Extract keywords
            const wordCounts: Record<string, number> = {};
            const stopWords = new Set(['the', 'and', 'is', 'in', 'to', 'of', 'it', 'for', 'a', 'this', 'that', 'on', 'with', 'as', 'at', 'by']);

            recentIssues.forEach(issue => {
                if (!issue.description) return;
                const words = issue.description.toLowerCase().replace(/[^a-z0-9\s]/g, '').split(/\s+/);
                words.forEach((word: string) => {
                    if (word && !stopWords.has(word)) {
                        wordCounts[word] = (wordCounts[word] || 0) + 1;
                    }
                });
            });

            const topKeywords = Object.entries(wordCounts)
                .sort((a, b) => b[1] - a[1])
                .slice(0, 5)
                .map(entry => entry[0]);

            // Detect category spikes
            // Get all issues for historical context (e.g. last 7 days)
            const weekAgoStr = new Date(last24HoursStart - 7 * 24 * 60 * 60 * 1000).toISOString().replace('T', ' ').substring(0, 19);
            const historicalStmt = db.prepare('SELECT category, count(*) as count FROM issues WHERE created_at >= ? AND created_at < ? GROUP BY category');
            const historicalCounts = historicalStmt.all(weekAgoStr, dateStr) as any[];

            const recentCategoryStmt = db.prepare('SELECT category, count(*) as count FROM issues WHERE created_at >= ? GROUP BY category');
            const recentCounts = recentCategoryStmt.all(dateStr) as any[];

            const historicalAvg: Record<string, number> = {};
            historicalCounts.forEach(row => {
                historicalAvg[row.category] = row.count / 7; // Average per day over 7 days
            });

            const categorySpikes: Record<string, { previousAvg: number; recent: number; spike: number }> = {};
            recentCounts.forEach(row => {
                const category = row.category;
                const recentCount = row.count;
                const avg = historicalAvg[category] || 0.1; // avoid division by zero
                const spike = recentCount / avg;

                if (spike > 1.5) { // 50% increase is a spike
                    categorySpikes[category] = { previousAvg: avg, recent: recentCount, spike };
                }
            });

            return { topKeywords, categorySpikes };
        } finally {
            db.close();
        }
    }
}
