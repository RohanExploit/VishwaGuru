import fs from 'fs';
import path from 'path';
import Database from 'better-sqlite3';
import { ModelWeights } from './adaptiveWeights';

export class PriorityEngine {
    private weightsPath: string;
    private dbPath: string;

    constructor(
        weightsPath: string = path.resolve(process.cwd(), 'data/modelWeights.json'),
        dbPath: string = path.resolve(process.cwd(), 'backend/data/issues.db')
    ) {
        this.weightsPath = weightsPath;
        this.dbPath = dbPath;
    }

    public adjustThresholds(last24HoursStart: number): void {
        const weightsData = JSON.parse(fs.readFileSync(this.weightsPath, 'utf8')) as ModelWeights;

        const db = new Database(this.dbPath, { readonly: true });

        try {
            // Analyze issue volume
            const dateStr = new Date(last24HoursStart).toISOString().replace('T', ' ').substring(0, 19);
            const stmt = db.prepare('SELECT count(*) as count FROM issues WHERE created_at >= ?');
            const result = stmt.get(dateStr) as any;

            const issueVolume = result.count || 0;

            let newThreshold = weightsData.duplicate_threshold;

            // If system is flooded, loosen duplicate detection (lower threshold to group more)
            // If very few issues, strict duplicate detection (higher threshold)
            if (issueVolume > 1000) {
                newThreshold = Math.max(0.6, weightsData.duplicate_threshold - 0.05);
            } else if (issueVolume < 100) {
                newThreshold = Math.min(0.9, weightsData.duplicate_threshold + 0.05);
            }

            if (newThreshold !== weightsData.duplicate_threshold) {
                const prevThreshold = weightsData.duplicate_threshold;
                weightsData.duplicate_threshold = newThreshold;

                weightsData.audit_history.push({
                    timestamp: new Date().toISOString(),
                    previous_threshold: prevThreshold,
                    new_threshold: newThreshold,
                    reason: `Adjusted based on issue volume (${issueVolume})`
                });

                if (weightsData.audit_history.length > 30) {
                    weightsData.audit_history = weightsData.audit_history.slice(-30);
                }

                fs.writeFileSync(this.weightsPath, JSON.stringify(weightsData, null, 2));
            }

        } finally {
            db.close();
        }
    }
}
