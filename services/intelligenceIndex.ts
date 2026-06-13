import sqlite3 from 'sqlite3';
import { Trends } from './trendAnalyzer';

export interface IndexResult {
    score: number;
    new_issues_count: number;
    resolved_issues_count: number;
    top_emerging_concern: string;
    highest_severity_region: string;
}

export class IntelligenceIndex {
    private dbPath: string;

    constructor(dbPath: string = './data/issues.db') {
        this.dbPath = dbPath;
    }

    private async getResolvedIssuesLast24h(): Promise<number> {
        return new Promise((resolve, reject) => {
            const db = new sqlite3.Database(this.dbPath, sqlite3.OPEN_READONLY, (err) => {
                if (err) return resolve(0);
            });

            const query = `
                SELECT COUNT(*) as resolved_count
                FROM issues
                WHERE resolved_at >= datetime('now', '-1 day')
            `;

            db.get(query, [], (err, row: any) => {
                db.close();
                if (err) {
                    if (err.message.includes("no such table")) return resolve(0);
                    return reject(err);
                }
                resolve(row ? row.resolved_count : 0);
            });
        });
    }

    public async generateDailyScore(trends: Trends): Promise<IndexResult> {
        const totalNew = trends.total_issues;
        const resolvedCount = await this.getResolvedIssuesLast24h();

        // Base 70 + 2 per resolution - 0.5 per new
        let score = 70.0 + (resolvedCount * 2.0) - (totalNew * 0.5);
        score = Math.max(0.0, Math.min(100.0, score));

        let topCat = "None";
        if (Object.keys(trends.category_distribution).length > 0) {
            topCat = Object.keys(trends.category_distribution).reduce((a, b) =>
                trends.category_distribution[a] > trends.category_distribution[b] ? a : b
            );
        }

        let highestSeverityRegion = "None";
        if (trends.clusters && trends.clusters.length > 0) {
            const topCluster = trends.clusters[0];
            highestSeverityRegion = `Lat ${topCluster.latitude.toFixed(4)}, Lon ${topCluster.longitude.toFixed(4)}`;
        }

        return {
            score: parseFloat(score.toFixed(1)),
            new_issues_count: totalNew,
            resolved_issues_count: resolvedCount,
            top_emerging_concern: topCat,
            highest_severity_region: highestSeverityRegion
        };
    }
}
