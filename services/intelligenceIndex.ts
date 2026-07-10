import fs from 'fs';
import path from 'path';
import Database from 'better-sqlite3';
import { TrendAnalysisResult } from './trendAnalyzer';

export interface Snapshot {
    date: string;
    civicIntelligenceIndex: number;
    indexChange: number;
    topEmergingConcern: string;
    highestSeverityRegion: string;
    metrics: {
        totalIssues: number;
        resolvedIssues: number;
        avgResolutionTimeDays: number | null;
    };
    trends: TrendAnalysisResult;
}

export class IntelligenceIndex {
    private dbPath: string;
    private snapshotsDir: string;

    constructor(
        dbPath: string = path.resolve(process.cwd(), 'backend/data/issues.db'),
        snapshotsDir: string = path.resolve(process.cwd(), 'data/dailySnapshots')
    ) {
        this.dbPath = dbPath;
        this.snapshotsDir = snapshotsDir;
    }

    public generateSnapshot(last24HoursStart: number, trends: TrendAnalysisResult): Snapshot {
        if (!fs.existsSync(this.snapshotsDir)) {
            fs.mkdirSync(this.snapshotsDir, { recursive: true });
        }

        const db = new Database(this.dbPath, { readonly: true });

        try {
            const dateStr = new Date(last24HoursStart).toISOString().replace('T', ' ').substring(0, 19);

            // Calculate total and resolved issues
            const statsStmt = db.prepare("SELECT count(*) as total, sum(case when status = 'Resolved' then 1 else 0 end) as resolved FROM issues WHERE created_at >= ?");
            const stats = statsStmt.get(dateStr) as any;

            const totalIssues = stats.total || 0;
            const resolvedIssues = stats.resolved || 0;

            // Region with highest severity (mocked using location with most critical/high upvotes)
            const regionStmt = db.prepare('SELECT location, sum(upvotes) as severity_score FROM issues WHERE created_at >= ? AND location IS NOT NULL GROUP BY location ORDER BY severity_score DESC LIMIT 1');
            const regionData = regionStmt.get(dateStr) as any;
            const highestSeverityRegion = regionData ? regionData.location : 'Unknown';

            // Top emerging concern (based on spikes)
            let topEmergingConcern = 'None';
            let maxSpike = 0;
            for (const [category, data] of Object.entries(trends.categorySpikes)) {
                if (data.spike > maxSpike) {
                    maxSpike = data.spike;
                    topEmergingConcern = category;
                }
            }

            if (topEmergingConcern === 'None' && trends.topKeywords.length > 0) {
                topEmergingConcern = trends.topKeywords[0] || 'None';
            }

            // Calculate Base Index (Simplified logic)
            // Base 50 + Bonus for resolution rate + Penalty for volume
            let indexScore = 50.0;
            if (totalIssues > 0) {
                indexScore += (resolvedIssues / totalIssues) * 30; // Up to 30 pts for resolution rate
            }

            // Check previous day for change
            const yesterdayStr = new Date(last24HoursStart - 24 * 60 * 60 * 1000).toISOString().split('T')[0] || '';
            const yesterdayFile = path.join(this.snapshotsDir, `${yesterdayStr}.json`);

            let indexChange = 0.0;
            if (fs.existsSync(yesterdayFile)) {
                const prevSnapshot = JSON.parse(fs.readFileSync(yesterdayFile, 'utf8')) as Snapshot;
                indexChange = indexScore - prevSnapshot.civicIntelligenceIndex;
            }

            const snapshot: Snapshot = {
                date: new Date(last24HoursStart).toISOString().split('T')[0],
                civicIntelligenceIndex: Number(indexScore.toFixed(1)),
                indexChange: Number(indexChange.toFixed(1)),
                topEmergingConcern,
                highestSeverityRegion,
                metrics: {
                    totalIssues,
                    resolvedIssues,
                    avgResolutionTimeDays: null
                },
                trends
            };

            const fileName = `${snapshot.date}.json`;
            const filePath = path.join(this.snapshotsDir, fileName);
            fs.writeFileSync(filePath, JSON.stringify(snapshot, null, 2));

            return snapshot;

        } finally {
            db.close();
        }
    }
}
