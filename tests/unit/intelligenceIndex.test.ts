import { IntelligenceIndex } from '../../services/intelligenceIndex';
import sqlite3 from 'sqlite3';
import { Trends } from '../../services/trendAnalyzer';

jest.mock('sqlite3', () => {
    return {
        OPEN_READONLY: 1,
        Database: jest.fn()
    };
});

describe('IntelligenceIndex', () => {
    let mockGet: jest.Mock;
    let mockClose: jest.Mock;

    beforeEach(() => {
        mockGet = jest.fn();
        mockClose = jest.fn();

        (sqlite3.Database as unknown as jest.Mock).mockImplementation((path, mode, callback) => {
            if (callback) callback(null);
            return {
                get: mockGet,
                close: mockClose
            };
        });
    });

    afterEach(() => {
        jest.clearAllMocks();
    });

    test('generateDailyScore calculates score correctly based on trends and db', async () => {
        const index = new IntelligenceIndex('test.db');

        mockGet.mockImplementation((query, params, callback) => {
            callback(null, { resolved_count: 5 }); // 5 resolved issues
        });

        const mockTrends: Trends = {
            top_keywords: [],
            category_distribution: { 'Pothole': 10, 'Garbage': 2 },
            clusters: [
                {
                    count: 4,
                    latitude: 19.0760,
                    longitude: 72.8777,
                    representative_category: 'Pothole',
                    representative_desc: 'Test'
                }
            ],
            spikes: [],
            total_issues: 12 // 12 new issues
        };

        const result = await index.generateDailyScore(mockTrends);

        // Score formula: 70.0 + (resolved * 2) - (new * 0.5)
        // Score: 70 + (5 * 2) - (12 * 0.5) = 70 + 10 - 6 = 74
        expect(result.score).toBe(74.0);
        expect(result.new_issues_count).toBe(12);
        expect(result.resolved_issues_count).toBe(5);
        expect(result.top_emerging_concern).toBe('Pothole');
        expect(result.highest_severity_region).toBe('Lat 19.0760, Lon 72.8777');
    });

    test('generateDailyScore clamps score between 0 and 100', async () => {
        const index = new IntelligenceIndex('test.db');

        // Force very high resolved count to exceed 100
        mockGet.mockImplementation((query, params, callback) => {
            callback(null, { resolved_count: 50 });
        });

        const mockTrends: Trends = {
            top_keywords: [],
            category_distribution: {},
            clusters: [],
            spikes: [],
            total_issues: 0
        };

        const result = await index.generateDailyScore(mockTrends);

        expect(result.score).toBe(100.0);
    });

    test('generateDailyScore handles no clusters and no categories gracefully', async () => {
        const index = new IntelligenceIndex('test.db');

        mockGet.mockImplementation((query, params, callback) => {
            callback(null, { resolved_count: 0 });
        });

        const mockTrends: Trends = {
            top_keywords: [],
            category_distribution: {},
            clusters: [],
            spikes: [],
            total_issues: 0
        };

        const result = await index.generateDailyScore(mockTrends);

        expect(result.score).toBe(70.0);
        expect(result.top_emerging_concern).toBe('None');
        expect(result.highest_severity_region).toBe('None');
    });
});
