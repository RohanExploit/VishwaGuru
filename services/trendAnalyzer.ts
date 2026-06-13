import sqlite3 from 'sqlite3';
import fs from 'fs';
import path from 'path';

export interface Cluster {
    count: number;
    latitude: number;
    longitude: number;
    representative_category: string;
    representative_desc: string;
}

export interface Trends {
    top_keywords: [string, number][];
    category_distribution: Record<string, number>;
    clusters: Cluster[];
    spikes: string[];
    total_issues: number;
}

export class TrendAnalyzer {
    private dbPath: string;
    private snapshotDir: string;
    private stopWords: Set<string>;

    constructor(dbPath: string = './data/issues.db', snapshotDir: string = './data/dailySnapshots') {
        this.dbPath = dbPath;
        this.snapshotDir = snapshotDir;
        this.stopWords = new Set([
            "the", "a", "an", "in", "on", "at", "to", "for", "of", "and", "is", "are",
            "was", "were", "this", "that", "it", "with", "from", "by", "as", "be",
            "or", "not", "but", "if", "so", "my", "your", "its", "their", "there",
            "here", "when", "where", "why", "how", "all", "any", "some", "no",
            "issue", "problem", "complaint", "regarding", "please", "help", "fix",
            "near", "opposite", "behind", "front", "road", "street", "lane"
        ]);
    }

    private async getIssuesLast24h(): Promise<any[]> {
        return new Promise((resolve, reject) => {
            const db = new sqlite3.Database(this.dbPath, sqlite3.OPEN_READONLY, (err) => {
                if (err) return resolve([]);
            });

            const query = `
                SELECT id, description, category, latitude, longitude, created_at
                FROM issues
                WHERE created_at >= datetime('now', '-1 day')
            `;

            db.all(query, [], (err, rows: any[]) => {
                db.close();
                if (err) {
                    if (err.message.includes("no such table")) return resolve([]);
                    return reject(err);
                }
                resolve(rows);
            });
        });
    }

    private extractKeywords(issues: any[]): [string, number][] {
        const text = issues.map(i => i.description || '').join(' ').toLowerCase();
        const words = text.match(/\b\w+\b/g) || [];

        const counts: Record<string, number> = {};
        for (const w of words) {
            if (!this.stopWords.has(w) && w.length > 2 && !/^\d+$/.test(w)) {
                counts[w] = (counts[w] || 0) + 1;
            }
        }

        const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1]);
        return sorted.slice(0, 5);
    }

    private extractCategories(issues: any[]): Record<string, number> {
        const counts: Record<string, number> = {};
        for (const issue of issues) {
            const cat = issue.category;
            if (cat) counts[cat] = (counts[cat] || 0) + 1;
        }
        return counts;
    }

    private _haversineDistance(lat1: number, lon1: number, lat2: number, lon2: number): number {
        const toRad = (x: number) => x * Math.PI / 180;
        const R = 6371e3; // Earth radius in meters
        const dLat = toRad(lat2 - lat1);
        const dLon = toRad(lon2 - lon1);
        const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
                  Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) *
                  Math.sin(dLon / 2) * Math.sin(dLon / 2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        return R * c;
    }

    private analyzeClusters(issues: any[]): Cluster[] {
        // Simple O(N^2) clustering based on proximity, returning clusters > 3 issues
        // Since this runs offline daily, performance is acceptable for moderate N.
        const clusters: any[][] = [];
        const visited = new Set<number>();

        const radiusMeters = 100.0;

        for (let i = 0; i < issues.length; i++) {
            if (visited.has(i)) continue;

            const cluster = [issues[i]];
            visited.add(i);

            for (let j = i + 1; j < issues.length; j++) {
                if (visited.has(j)) continue;

                if (issues[i].latitude && issues[i].longitude && issues[j].latitude && issues[j].longitude) {
                    const dist = this._haversineDistance(
                        issues[i].latitude, issues[i].longitude,
                        issues[j].latitude, issues[j].longitude
                    );

                    if (dist <= radiusMeters) {
                        cluster.push(issues[j]);
                        visited.add(j);
                    }
                }
            }

            if (cluster.length >= 3) {
                clusters.push(cluster);
            }
        }

        const results: Cluster[] = clusters.map(c => ({
            count: c.length,
            latitude: c[0].latitude,
            longitude: c[0].longitude,
            representative_category: c[0].category,
            representative_desc: c[0].description ? c[0].description.substring(0, 50) + '...' : ''
        }));

        return results.sort((a, b) => b.count - a.count);
    }

    private getPreviousDistribution(): Record<string, number> {
        try {
            if (!fs.existsSync(this.snapshotDir)) return {};
            const files = fs.readdirSync(this.snapshotDir).filter(f => f.endsWith('.json')).sort();
            if (files.length === 0) return {};
            const latest = files[files.length - 1];
            const data = JSON.parse(fs.readFileSync(path.join(this.snapshotDir, latest), 'utf-8'));
            return data.trends?.category_distribution || {};
        } catch (e) {
            console.error("Error reading previous snapshot for trends", e);
            return {};
        }
    }

    private detectSpikes(currentDist: Record<string, number>, previousDist: Record<string, number>): string[] {
        const spikes: string[] = [];
        for (const [category, count] of Object.entries(currentDist)) {
            const prevCount = previousDist[category] || 0;
            if (prevCount > 0 && count > 5) {
                const increase = (count - prevCount) / prevCount;
                if (increase > 0.5) spikes.push(category);
            } else if (prevCount === 0 && count > 5) {
                spikes.push(category);
            }
        }
        return spikes;
    }

    public async analyze(): Promise<{ issues: any[], trends: Trends }> {
        const issues = await this.getIssuesLast24h();
        const keywords = this.extractKeywords(issues);
        const distribution = this.extractCategories(issues);
        const clusters = this.analyzeClusters(issues);

        const previousDist = this.getPreviousDistribution();
        const spikes = this.detectSpikes(distribution, previousDist);

        return {
            issues,
            trends: {
                top_keywords: keywords,
                category_distribution: distribution,
                clusters,
                spikes,
                total_issues: issues.length
            }
        };
    }
}
