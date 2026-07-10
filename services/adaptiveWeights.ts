import fs from 'fs';
import path from 'path';
import Database from 'better-sqlite3';

export interface ModelWeights {
    severity_weights: Record<string, number>;
    duplicate_threshold: number;
    audit_history: any[];
}

export class AdaptiveWeights {
    private weightsPath: string;
    private dbPath: string;

    constructor(
        weightsPath: string = path.resolve(process.cwd(), 'data/modelWeights.json'),
        dbPath: string = path.resolve(process.cwd(), 'backend/data/issues.db')
    ) {
        this.weightsPath = weightsPath;
        this.dbPath = dbPath;
    }

    public optimize(last24HoursStart: number): void {
        const weightsData = JSON.parse(fs.readFileSync(this.weightsPath, 'utf8')) as ModelWeights;
        const currentWeights = { ...weightsData.severity_weights };

        const db = new Database(this.dbPath, { readonly: true });

        try {
            // Find categories with high upvotes or critical status
            const dateStr = new Date(last24HoursStart).toISOString().replace('T', ' ').substring(0, 19);

            // Adjust weights based on total upvotes in the category
            const stmt = db.prepare('SELECT category, SUM(upvotes) as total_upvotes, COUNT(*) as issue_count FROM issues WHERE created_at >= ? GROUP BY category');
            const metrics = stmt.all(dateStr) as any[];

            let weightsChanged = false;

            metrics.forEach(row => {
                const category = row.category;
                const totalUpvotes = row.total_upvotes || 0;
                const issueCount = row.issue_count || 1;
                const upvoteRatio = totalUpvotes / issueCount;

                if (!weightsData.severity_weights[category]) {
                    weightsData.severity_weights[category] = 1.0;
                }

                // If upvotes are consistently high, slightly increase the severity weight for this category
                if (upvoteRatio > 10) {
                    weightsData.severity_weights[category] = Math.min(2.0, weightsData.severity_weights[category] + 0.1);
                    weightsChanged = true;
                } else if (upvoteRatio < 2 && weightsData.severity_weights[category] > 1.0) {
                     // Decay back towards 1.0 if not heavily upvoted anymore
                     weightsData.severity_weights[category] = Math.max(1.0, weightsData.severity_weights[category] - 0.05);
                     weightsChanged = true;
                }
            });

            if (weightsChanged) {
                // Save to audit history
                weightsData.audit_history.push({
                    timestamp: new Date().toISOString(),
                    previous_weights: currentWeights,
                    reason: "Automated daily upvote/severity adjustment"
                });

                // Keep only last 30 audits
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
