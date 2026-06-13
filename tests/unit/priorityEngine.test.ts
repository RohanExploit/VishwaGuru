import { PriorityEngine } from '../../services/priorityEngine';
import sqlite3 from 'sqlite3';

jest.mock('sqlite3', () => {
    return {
        OPEN_READONLY: 1,
        Database: jest.fn()
    };
});

describe('PriorityEngine', () => {
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
    });

    afterEach(() => {
        jest.clearAllMocks();
    });

    test('autoAdjustSeverity should return updates when a category is upgraded >= 3 times', async () => {
        const engine = new PriorityEngine('test.db');

        mockAll.mockImplementation((query, params, callback) => {
            callback(null, [
                { category: 'Pothole', upgrade_count: 5 },
                { category: 'Water', upgrade_count: 2 }
            ]);
        });

        const updates = await engine.autoAdjustSeverity();

        expect(updates).toHaveLength(1);
        expect(updates[0].category).toBe('Pothole');
        expect(updates[0].factor).toBe(1.1);
        expect(updates[0].reason).toContain('5');
    });

    test('autoAdjustSeverity should return empty array when no category is upgraded >= 3 times', async () => {
        const engine = new PriorityEngine('test.db');

        mockAll.mockImplementation((query, params, callback) => {
            callback(null, [
                { category: 'Pothole', upgrade_count: 2 },
                { category: 'Water', upgrade_count: 1 }
            ]);
        });

        const updates = await engine.autoAdjustSeverity();

        expect(updates).toHaveLength(0);
    });

    test('autoAdjustSeverity should handle missing tables gracefully', async () => {
        const engine = new PriorityEngine('test.db');

        mockAll.mockImplementation((query, params, callback) => {
            callback(new Error('SQLITE_ERROR: no such table: escalation_audits'), []);
        });

        const updates = await engine.autoAdjustSeverity();

        expect(updates).toHaveLength(0);
    });
});
