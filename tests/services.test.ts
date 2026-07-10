import fs from 'fs';
import path from 'path';
import Database from 'better-sqlite3';
import { TrendAnalyzer } from '../services/trendAnalyzer';
import { AdaptiveWeights } from '../services/adaptiveWeights';
import { PriorityEngine } from '../services/priorityEngine';
import { IntelligenceIndex } from '../services/intelligenceIndex';

describe('Daily Civic Intelligence Refinement Engine', () => {
    const testDbPath = path.resolve(__dirname, 'test_issues.db');
    const testWeightsPath = path.resolve(__dirname, 'test_weights.json');
    const testSnapshotsDir = path.resolve(__dirname, 'dailySnapshots');

    beforeAll(() => {
        // Setup mock database
        const db = new Database(testDbPath);
        db.exec(`
            CREATE TABLE IF NOT EXISTS issues (
                id INTEGER PRIMARY KEY,
                description TEXT,
                category TEXT,
                status TEXT,
                upvotes INTEGER,
                location TEXT,
                created_at DATETIME
            );
        `);

        const nowStr = new Date().toISOString().replace('T', ' ').substring(0, 19);
        const yesterdayStr = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString().replace('T', ' ').substring(0, 19);

        const insert = db.prepare('INSERT INTO issues (description, category, status, upvotes, location, created_at) VALUES (?, ?, ?, ?, ?, ?)');

        insert.run('Huge pothole on main street, dangerous!', 'Pothole', 'Open', 15, 'Ward 1', nowStr);
        insert.run('Another pothole here.', 'Pothole', 'Open', 20, 'Ward 1', nowStr); // Total 35 upvotes for 2 issues (ratio 17.5 > 10)
        insert.run('No water supply for 2 days', 'Water Supply', 'Resolved', 5, 'Ward 2', nowStr);
        insert.run('Water leaking from pipe', 'Water Supply', 'Open', 1, 'Ward 2', nowStr);

        // Historical data for spikes
        for(let i = 0; i < 5; i++) {
             insert.run('Old garbage issue', 'Garbage', 'Resolved', 0, 'Ward 3', yesterdayStr);
        }

        db.close();

        // Setup mock weights file
        fs.writeFileSync(testWeightsPath, JSON.stringify({
            severity_weights: { "Pothole": 1.0, "Water Supply": 1.0 },
            duplicate_threshold: 0.8,
            audit_history: []
        }));

        // Setup snapshots dir
        if (!fs.existsSync(testSnapshotsDir)) {
            fs.mkdirSync(testSnapshotsDir);
        }
    });

    afterAll(() => {
        // Cleanup
        if (fs.existsSync(testDbPath)) fs.unlinkSync(testDbPath);
        if (fs.existsSync(testWeightsPath)) fs.unlinkSync(testWeightsPath);
        if (fs.existsSync(testSnapshotsDir)) {
            fs.readdirSync(testSnapshotsDir).forEach(f => fs.unlinkSync(path.join(testSnapshotsDir, f)));
            fs.rmdirSync(testSnapshotsDir);
        }
    });

    const getTestTime = () => Date.now() - (12 * 60 * 60 * 1000); // 12 hours ago

    test('TrendAnalyzer extracts keywords and detects spikes', () => {
        const analyzer = new TrendAnalyzer(testDbPath);
        const result = analyzer.analyze(getTestTime());

        expect(result.topKeywords).toContain('pothole');
        expect(result.topKeywords).toContain('water');
        expect(Object.keys(result.categorySpikes)).toContain('Pothole');
        expect(Object.keys(result.categorySpikes)).toContain('Water Supply');
    });

    test('AdaptiveWeights adjusts weights based on upvotes', () => {
        const optimizer = new AdaptiveWeights(testWeightsPath, testDbPath);
        optimizer.optimize(getTestTime());

        const weights = JSON.parse(fs.readFileSync(testWeightsPath, 'utf8'));
        expect(weights.severity_weights['Pothole']).toBeGreaterThan(1.0);
    });

    test('PriorityEngine adjusts thresholds based on volume', () => {
        const engine = new PriorityEngine(testWeightsPath, testDbPath);
        engine.adjustThresholds(getTestTime());

        const weights = JSON.parse(fs.readFileSync(testWeightsPath, 'utf8'));
        expect(weights.duplicate_threshold).toBeLessThan(0.86); // Should go up to 0.85
        expect(weights.duplicate_threshold).toBeGreaterThan(0.8);
    });

    test('IntelligenceIndex generates snapshot', () => {
        const index = new IntelligenceIndex(testDbPath, testSnapshotsDir);
        const trends = { topKeywords: ['pothole'], categorySpikes: { 'Pothole': { previousAvg: 1, recent: 2, spike: 2 } } };

        const snapshot = index.generateSnapshot(getTestTime(), trends);

        expect(snapshot.civicIntelligenceIndex).toBeGreaterThan(40);
        expect(snapshot.topEmergingConcern).toBe('Pothole');
        expect(snapshot.highestSeverityRegion).toBe('Ward 1'); // Ward 1 has most upvotes in test data

        const fileName = `${snapshot.date}.json`;
        expect(fs.existsSync(path.join(testSnapshotsDir, fileName))).toBe(true);
    });
});
