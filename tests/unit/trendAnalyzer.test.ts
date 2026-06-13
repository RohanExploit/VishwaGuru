import { TrendAnalyzer } from '../../services/trendAnalyzer';
import sqlite3 from 'sqlite3';
import fs from 'fs';

jest.mock('sqlite3', () => {
    return {
        OPEN_READONLY: 1,
        Database: jest.fn()
    };
});

jest.mock('fs');

describe('TrendAnalyzer', () => {
    let mockAll: jest.Mock;
    let mockClose: jest.Mock;

    beforeEach(() => {
        mockAll = jest.fn();
        mockClose = jest.fn();

        (sqlite3.Database as unknown as jest.Mock).mockImplementation((path, mode, callback) => {
            if (callback) callback(null);
            return {
                all: mockAll,
                close: mockClose
            };
        });

        // Mock fs functions
        (fs.existsSync as jest.Mock).mockReturnValue(true);
        (fs.readdirSync as jest.Mock).mockReturnValue(['2026-02-15.json']);
        (fs.readFileSync as jest.Mock).mockReturnValue(JSON.stringify({
            trends: {
                category_distribution: {
                    'Pothole': 2,
                    'Water Supply': 1
                }
            }
        }));
    });

    afterEach(() => {
        jest.clearAllMocks();
    });

    test('analyze should extract keywords and categories correctly', async () => {
        const analyzer = new TrendAnalyzer('test.db', 'snapshots');

        mockAll.mockImplementation((query, params, callback) => {
            callback(null, [
                { id: 1, description: 'big pothole dangerous pothole', category: 'Pothole', latitude: 10, longitude: 10 },
                { id: 2, description: 'pothole causing accident', category: 'Pothole', latitude: 10, longitude: 10.0001 },
                { id: 3, description: 'water leaking from pipe pipe pipe', category: 'Water Supply', latitude: 20, longitude: 20 },
                { id: 4, description: 'dangerous pothole', category: 'Pothole', latitude: 10, longitude: 10.0002 },
                { id: 5, description: 'dangerous pothole', category: 'Pothole', latitude: 10, longitude: 10.0003 },
                { id: 6, description: 'dangerous pothole', category: 'Pothole', latitude: 10, longitude: 10.0004 },
                { id: 7, description: 'dangerous pothole', category: 'Pothole', latitude: 10, longitude: 10.0005 }
            ]); // Added more Pothole entries to trigger spike detection
        });

        const result = await analyzer.analyze();

        expect(result.issues).toHaveLength(7);
        expect(result.trends.total_issues).toBe(7);

        const keywords = Object.fromEntries(result.trends.top_keywords);
        expect(keywords['pothole']).toBe(7); // Used 7 times
        expect(keywords['dangerous']).toBe(5);

        expect(result.trends.category_distribution['Pothole']).toBe(6);
        expect(result.trends.category_distribution['Water Supply']).toBe(1);

        // Pothole went from 2 to 6, so it's a spike
        expect(result.trends.spikes).toContain('Pothole');

        // Clustering: The 6 pothole issues are very close to each other
        expect(result.trends.clusters.length).toBeGreaterThanOrEqual(1);
        expect(result.trends.clusters[0].count).toBe(6);
        expect(result.trends.clusters[0].representative_category).toBe('Pothole');
    });

    test('analyze should handle empty database gracefully', async () => {
        const analyzer = new TrendAnalyzer('test.db', 'snapshots');

        mockAll.mockImplementation((query, params, callback) => {
            callback(null, []);
        });

        const result = await analyzer.analyze();

        expect(result.issues).toHaveLength(0);
        expect(result.trends.total_issues).toBe(0);
        expect(result.trends.top_keywords).toHaveLength(0);
    });
});
