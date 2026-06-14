import * as sqlite3 from 'sqlite3';
import * as fs from 'fs';
import * as path from 'path';

// Import services after setting up env vars
import { PriorityEngine } from '../services/priorityEngine';

describe('Daily Refinement Job System Tests', () => {
    let db: sqlite3.Database;
    const testDbPath = path.resolve(__dirname, '../data/test_issues.db');
    const snapshotsDir = path.resolve(__dirname, '../data/test_job_snapshots');
    const weightsPath = path.resolve(__dirname, '../data/test_job_weights.json');
    let engine: PriorityEngine;

    beforeAll(async () => {
        // Setup environments
        process.env.DB_PATH = testDbPath;
        process.env.SNAPSHOTS_DIR = snapshotsDir;
        process.env.WEIGHTS_PATH = weightsPath;

        // Clean existing files
        if (fs.existsSync(testDbPath)) fs.unlinkSync(testDbPath);
        if (fs.existsSync(weightsPath)) fs.unlinkSync(weightsPath);
        if (fs.existsSync(snapshotsDir)) {
            const files = fs.readdirSync(snapshotsDir);
            for (const file of files) fs.unlinkSync(path.join(snapshotsDir, file));
            fs.rmdirSync(snapshotsDir);
        }

        // Initialize DB
        db = new sqlite3.Database(testDbPath);

        const runAsync = (query: string, params: any[] = []): Promise<void> => {
            return new Promise((resolve, reject) => {
                db.run(query, params, (err) => {
                    if (err) reject(err);
                    else resolve();
                });
            });
        };

        // Create mock issues table
        await runAsync(`
            CREATE TABLE IF NOT EXISTS issues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT,
                category TEXT,
                latitude REAL,
                longitude REAL,
                created_at DATETIME
            )
        `);

        // Insert mock data (simulate 48 hours)
        const now = new Date();
        const yesterdayStr = new Date(now.getTime() - 12 * 60 * 60 * 1000).toISOString(); // 12 hours ago
        const twoDaysAgoStr = new Date(now.getTime() - 36 * 60 * 60 * 1000).toISOString(); // 36 hours ago

        // Older issues
        await runAsync(`INSERT INTO issues (description, category, created_at) VALUES ('Old pothole', 'pothole', ?)`, [twoDaysAgoStr]);
        await runAsync(`INSERT INTO issues (description, category, created_at) VALUES ('Old garbage', 'garbage', ?)`, [twoDaysAgoStr]);

        // Recent issues
        await runAsync(`INSERT INTO issues (description, category, latitude, longitude, created_at) VALUES ('Huge pothole near main road', 'pothole', 19.07, 72.87, ?)`, [yesterdayStr]);
        await runAsync(`INSERT INTO issues (description, category, latitude, longitude, created_at) VALUES ('Pothole causing traffic', 'pothole', 19.07, 72.87, ?)`, [yesterdayStr]);
        await runAsync(`INSERT INTO issues (description, category, latitude, longitude, created_at) VALUES ('Another pothole', 'pothole', 19.07, 72.87, ?)`, [yesterdayStr]);
        await runAsync(`INSERT INTO issues (description, category, latitude, longitude, created_at) VALUES ('Streetlight broken', 'streetlight', 18.52, 73.85, ?)`, [yesterdayStr]);

        engine = new PriorityEngine();
    });

    afterAll(() => {
        db.close();
        if (fs.existsSync(testDbPath)) fs.unlinkSync(testDbPath);
        if (fs.existsSync(weightsPath)) fs.unlinkSync(weightsPath);
        if (fs.existsSync(snapshotsDir)) {
            const files = fs.readdirSync(snapshotsDir);
            for (const file of files) fs.unlinkSync(path.join(snapshotsDir, file));
            fs.rmdirSync(snapshotsDir);
        }
    });

    it('should complete the daily refinement and update artifacts', async () => {
        // Run job
        const snapshot = await engine.runDailyRefinement();

        // 1. Check generated snapshot logic
        expect(snapshot.topKeywords).toContain('pothole');
        expect(snapshot.topEmergingConcern).toBe('pothole'); // Spiked 200% (1 -> 3)
        expect(snapshot.highestSeverityRegion).toBe('19.07,72.87');

        // 2. Check weight adjustments
        const updatedWeights = JSON.parse(fs.readFileSync(weightsPath, 'utf8'));

        // Pothole should increase due to >100% spike
        expect(updatedWeights.severityWeights['pothole']).toBeGreaterThan(5); // Default is 5

        // Duplicate threshold should decrease due to clustering
        expect(updatedWeights.duplicateThreshold).toBeLessThan(0.8);

        // 3. Verify snapshot was saved to disk
        const todayStr = new Date().toISOString().split('T')[0];
        const snapshotFile = path.join(snapshotsDir, `${todayStr}.json`);
        expect(fs.existsSync(snapshotFile)).toBe(true);

        const savedSnapshot = JSON.parse(fs.readFileSync(snapshotFile, 'utf8'));
        expect(savedSnapshot.topEmergingConcern).toBe('pothole');
    });
});
