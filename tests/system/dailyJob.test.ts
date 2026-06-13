import { DailyRefinementJob } from '../../scheduler/dailyRefinementJob';
import sqlite3 from 'sqlite3';
import fs from 'fs';
import path from 'path';

jest.mock('sqlite3', () => {
    return {
        OPEN_READONLY: 1,
        Database: jest.fn()
    };
});

describe('System Test: Daily Refinement Job', () => {
    const TEMP_SNAPSHOT_DIR = './tests/temp_snapshots';
    const TEMP_WEIGHTS_FILE = './tests/temp_modelWeights.json';

    let mockAll: jest.Mock;
    let mockGet: jest.Mock;
    let mockClose: jest.Mock;

    beforeAll(() => {
        if (!fs.existsSync('./tests')) fs.mkdirSync('./tests');
        if (!fs.existsSync(TEMP_SNAPSHOT_DIR)) fs.mkdirSync(TEMP_SNAPSHOT_DIR);
    });

    afterAll(() => {
        if (fs.existsSync(TEMP_SNAPSHOT_DIR)) {
            fs.readdirSync(TEMP_SNAPSHOT_DIR).forEach(file => fs.unlinkSync(path.join(TEMP_SNAPSHOT_DIR, file)));
            fs.rmdirSync(TEMP_SNAPSHOT_DIR);
        }
        if (fs.existsSync(TEMP_WEIGHTS_FILE)) {
            fs.unlinkSync(TEMP_WEIGHTS_FILE);
        }
    });

    beforeEach(() => {
        // Reset the weights file to default before each test
        fs.writeFileSync(TEMP_WEIGHTS_FILE, JSON.stringify({
            category_multipliers: { 'Garbage': 1.0 },
            duplicate_search_radius: 50.0,
            audit_history: []
        }));

        mockAll = jest.fn();
        mockGet = jest.fn();
        mockClose = jest.fn();

        (sqlite3.Database as unknown as jest.Mock).mockImplementation((path, mode, callback) => {
            if (callback) callback(null);
            return {
                all: mockAll,
                get: mockGet,
                close: mockClose
            };
        });
    });

    afterEach(() => {
        jest.clearAllMocks();
    });

    test('runCycle generates snapshot and updates weights end-to-end', async () => {
        const job = new DailyRefinementJob('dummy.db', TEMP_SNAPSHOT_DIR, TEMP_WEIGHTS_FILE);

        // Mock DB calls
        mockAll.mockImplementation((query, params, callback) => {
            if (query.includes('FROM issues')) {
                callback(null, [
                    { id: 1, description: 'trash everywhere', category: 'Garbage', latitude: 12, longitude: 12 },
                    { id: 2, description: 'so much garbage', category: 'Garbage', latitude: 12, longitude: 12.0001 }
                ]);
            } else if (query.includes('FROM escalation_audits')) {
                callback(null, [
                    { category: 'Garbage', upgrade_count: 5 } // Above threshold (3)
                ]);
            }
        });

        mockGet.mockImplementation((query, params, callback) => {
            callback(null, { resolved_count: 10 });
        });

        // Suppress console.log for clean test output
        const logSpy = jest.spyOn(console, 'log').mockImplementation(() => {});

        // Run the daily cycle
        await job.runCycle();

        logSpy.mockRestore();

        // 1. Assert snapshot file was created
        const files = fs.readdirSync(TEMP_SNAPSHOT_DIR);
        expect(files.length).toBeGreaterThan(0);

        const latestFile = files[files.length - 1];
        const snapshotContent = JSON.parse(fs.readFileSync(path.join(TEMP_SNAPSHOT_DIR, latestFile), 'utf-8'));

        expect(snapshotContent.date).toBeDefined();
        expect(snapshotContent.civic_index.score).toBeDefined();
        // 70 + (10 * 2) - (2 * 0.5) = 70 + 20 - 1 = 89
        expect(snapshotContent.civic_index.score).toBe(89.0);
        expect(snapshotContent.trends.total_issues).toBe(2);

        // Assert weight changes were logged in snapshot
        // Since there are only 2 issues and 0 clusters, the duplicate pattern logic:
        // if clusterCount === 0 && issuesCount > 50 -> factor = 1.05
        // if issuesCount < 10 && currentRadius > 50 -> factor = 0.95
        // issuesCount is 2. currentRadius is 50. Neither condition triggers a radius change.
        // Therefore, weight_changes should have length 1 (only the category multiplier)
        expect(snapshotContent.weight_changes).toHaveLength(1); // Category multiplier only
        expect(snapshotContent.weight_changes[0].category).toBe('Garbage');

        // 2. Assert modelWeights.json was updated
        const weightsContent = JSON.parse(fs.readFileSync(TEMP_WEIGHTS_FILE, 'utf-8'));

        expect(weightsContent.category_multipliers['Garbage']).toBe(1.1); // Increased by 10%
        expect(weightsContent.audit_history.length).toBeGreaterThan(0);
        expect(weightsContent.audit_history[0].key).toBe('category_multipliers.Garbage');
        expect(weightsContent.audit_history[0].newValue).toBe(1.1);
    });
});
