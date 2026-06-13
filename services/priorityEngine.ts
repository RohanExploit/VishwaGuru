import sqlite3 from 'sqlite3';

export interface WeightUpdate {
    category: string;
    factor: number;
    reason: string;
}

/**
 * priorityEngine
 * Analyzes manual critical markings (escalations) in the database
 * to auto-adjust severity scoring parameters.
 */
export class PriorityEngine {
    private dbPath: string;

    constructor(dbPath: string = './data/issues.db') {
        this.dbPath = dbPath;
    }

    /**
     * Finds manual severity upgrades in the last 24h and calculates new weight parameters
     */
    public async autoAdjustSeverity(): Promise<WeightUpdate[]> {
        return new Promise((resolve, reject) => {
            const db = new sqlite3.Database(this.dbPath, sqlite3.OPEN_READONLY, (err) => {
                if (err) {
                    console.error('Error opening database', err);
                    // For testing/mocking, if DB doesn't exist, just return empty
                    return resolve([]);
                }
            });

            // SQLite query to find count of 'SEVERITY_UPGRADE' per category in the last 24h
            // Assuming tables `escalation_audits` and `grievances` exist.
            const query = `
                SELECT g.category, COUNT(e.id) as upgrade_count
                FROM escalation_audits e
                JOIN grievances g ON e.grievance_id = g.id
                WHERE e.reason = 'SEVERITY_UPGRADE'
                  AND e.timestamp >= datetime('now', '-1 day')
                GROUP BY g.category
            `;

            db.all(query, [], (err, rows: any[]) => {
                db.close();
                if (err) {
                    // If tables don't exist yet, gracefully return empty updates
                    if (err.message.includes("no such table")) {
                        return resolve([]);
                    }
                    console.error("Error executing query in priorityEngine:", err);
                    return reject(err);
                }

                const updates: WeightUpdate[] = [];
                for (const row of rows) {
                    const count = row.upgrade_count;
                    const category = row.category;

                    // If marked critical >= 3 times in 24h, increase weight by 10%
                    if (count >= 3 && category) {
                        updates.push({
                            category,
                            factor: 1.1,
                            reason: `Manual severity upgrades count: ${count}`
                        });
                    }
                }

                resolve(updates);
            });
        });
    }
}
