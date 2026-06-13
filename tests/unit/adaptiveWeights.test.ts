import { AdaptiveWeights } from '../../services/adaptiveWeights';
import fs from 'fs';

jest.mock('fs');
jest.mock('sqlite3', () => {
    return {
        OPEN_READONLY: 1,
        Database: jest.fn()
    };
});

describe('AdaptiveWeights', () => {
    let mockExistsSync: jest.Mock;
    let mockReadFileSync: jest.Mock;
    let mockWriteFileSync: jest.Mock;

    beforeEach(() => {
        mockExistsSync = fs.existsSync as jest.Mock;
        mockReadFileSync = fs.readFileSync as jest.Mock;
        mockWriteFileSync = fs.writeFileSync as jest.Mock;

        mockExistsSync.mockReturnValue(true);
        mockReadFileSync.mockReturnValue(JSON.stringify({
            category_multipliers: {
                'Pothole': 1.0,
                'Garbage': 1.5
            },
            duplicate_search_radius: 50.0,
            audit_history: []
        }));
    });

    afterEach(() => {
        jest.clearAllMocks();
    });

    test('updateCategoryWeights should update weight and record audit', () => {
        const adaptiveWeights = new AdaptiveWeights('dummy.json');

        const updates = [
            { category: 'Pothole', factor: 1.1, reason: 'test reason' }
        ];

        const changes = adaptiveWeights.updateCategoryWeights(updates);

        expect(changes).toHaveLength(1);
        expect(changes[0].new_weight).toBeCloseTo(1.1);

        const weights = adaptiveWeights.getWeights();
        expect(weights.category_multipliers['Pothole']).toBeCloseTo(1.1);
        expect(weights.audit_history).toHaveLength(1);
        expect(weights.audit_history[0].key).toBe('category_multipliers.Pothole');
        expect(weights.audit_history[0].oldValue).toBe(1.0);
        expect(weights.audit_history[0].newValue).toBeCloseTo(1.1);

        expect(mockWriteFileSync).toHaveBeenCalled();
    });

    test('updateDuplicateRadius should increase radius if high cluster density', () => {
        const adaptiveWeights = new AdaptiveWeights('dummy.json');

        const change = adaptiveWeights.updateDuplicateRadius(6, 60);

        expect(change).not.toBeNull();
        expect(change?.new_weight).toBe(52.5); // 50 * 1.05

        const weights = adaptiveWeights.getWeights();
        expect(weights.duplicate_search_radius).toBe(52.5);
        expect(weights.audit_history).toHaveLength(1);
        expect(weights.audit_history[0].key).toBe('duplicate_search_radius');
        expect(weights.audit_history[0].oldValue).toBe(50.0);
        expect(weights.audit_history[0].newValue).toBe(52.5);

        expect(mockWriteFileSync).toHaveBeenCalled();
    });

    test('updateDuplicateRadius should clamp radius bounds', () => {
        const adaptiveWeights = new AdaptiveWeights('dummy.json');

        // Set radius near maximum
        adaptiveWeights.getWeights().duplicate_search_radius = 195.0;

        const change = adaptiveWeights.updateDuplicateRadius(6, 60);

        expect(change).not.toBeNull();
        expect(change?.new_weight).toBe(200.0); // Clamped

        const weights = adaptiveWeights.getWeights();
        expect(weights.duplicate_search_radius).toBe(200.0);
    });

    test('initialize correctly when file does not exist', () => {
        mockExistsSync.mockReturnValue(false);

        const adaptiveWeights = new AdaptiveWeights('dummy.json');
        const weights = adaptiveWeights.getWeights();

        expect(weights).toBeDefined();
        expect(weights.category_multipliers).toBeDefined();
        expect(weights.audit_history).toEqual([]);
    });
});
