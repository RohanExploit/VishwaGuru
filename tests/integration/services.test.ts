import { TrendAnalyzer } from '../../services/trendAnalyzer';
import { PriorityEngine } from '../../services/priorityEngine';
import { AdaptiveWeights } from '../../services/adaptiveWeights';
import { IntelligenceIndex } from '../../services/intelligenceIndex';
import sqlite3 from 'sqlite3';
import fs from 'fs';

jest.mock('sqlite3', () => {
    return {
        OPEN_READONLY: 1,
        Database: jest.fn()
    };
});

jest.mock('fs');

describe('Services Integration', () => {
    let mockAll: jest.Mock;
    let mockGet: jest.Mock;
    let mockClose: jest.Mock;

    beforeEach(() => {
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

        // FS mocks
        (fs.existsSync as jest.Mock).mockReturnValue(true);
        (fs.readdirSync as jest.Mock).mockReturnValue(['mock.json']);
        (fs.readFileSync as jest.Mock).mockReturnValue(JSON.stringify({
            category_multipliers: { 'Pothole': 1.0 },
            duplicate_search_radius: 50.0,
            audit_history: []
        }));
    });

    afterEach(() => {
        jest.clearAllMocks();
    });

    test('Data flows correctly from analyzer to index and weight updates', async () => {
        // Setup mock data
        mockAll.mockImplementation((query, params, callback) => {
            if (query.includes('FROM issues')) {
                // Trend Analyzer mock
                callback(null, [
                    { id: 1, description: 'bad pothole here', category: 'Pothole', latitude: 10, longitude: 10 },
                    { id: 2, description: 'bad pothole here too', category: 'Pothole', latitude: 10, longitude: 10.0001 }
                ]);
            } else if (query.includes('FROM escalation_audits')) {
                // Priority Engine mock
                callback(null, [
                    { category: 'Pothole', upgrade_count: 4 }
                ]);
            }
        });

        mockGet.mockImplementation((query, params, callback) => {
            // Intelligence Index mock
            callback(null, { resolved_count: 3 });
        });

        // Initialize Services
        const trendAnalyzer = new TrendAnalyzer('dummy.db', 'dummyDir');
        const priorityEngine = new PriorityEngine('dummy.db');
        const adaptiveWeights = new AdaptiveWeights('dummy.json');
        const intelligenceIndex = new IntelligenceIndex('dummy.db');

        // 1. Analyze Trends
        const { issues, trends } = await trendAnalyzer.analyze();

        expect(issues).toHaveLength(2);
        expect(trends.total_issues).toBe(2);
        expect(trends.category_distribution['Pothole']).toBe(2);

        // 2. Generate Intelligence Index (Flow: Trends -> Index)
        const indexResult = await intelligenceIndex.generateDailyScore(trends);

        // 70 + (3 * 2) - (2 * 0.5) = 70 + 6 - 1 = 75
        expect(indexResult.score).toBe(75.0);
        expect(indexResult.top_emerging_concern).toBe('Pothole');

        // 3. Weight Updates (Flow: Priority Engine -> Adaptive Weights)
        const weightUpdates = await priorityEngine.autoAdjustSeverity();
        expect(weightUpdates).toHaveLength(1);
        expect(weightUpdates[0].category).toBe('Pothole');
        expect(weightUpdates[0].factor).toBe(1.1);

        const changes = adaptiveWeights.updateCategoryWeights(weightUpdates);
        expect(changes).toHaveLength(1);
        expect(changes[0].category).toBe('Pothole');
        expect(changes[0].new_weight).toBe(1.1); // from default 1.0
    });
});
