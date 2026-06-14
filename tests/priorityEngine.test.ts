import { PriorityEngine } from '../services/priorityEngine';
import * as path from 'path';
import * as fs from 'fs';

// Mock dependencies
jest.mock('../services/trendAnalyzer');
jest.mock('../services/adaptiveWeights');
jest.mock('../services/intelligenceIndex');

import { TrendAnalyzer } from '../services/trendAnalyzer';
import { AdaptiveWeights } from '../services/adaptiveWeights';
import { IntelligenceIndex } from '../services/intelligenceIndex';

describe('PriorityEngine Integration Tests', () => {
    let engine: PriorityEngine;

    beforeEach(() => {
        // Reset mocks
        jest.clearAllMocks();

        // Mock implementations
        (TrendAnalyzer.prototype.analyzeLast24h as jest.Mock).mockResolvedValue({
            topKeywords: ['pothole', 'leak'],
            categorySpikes: { 'water_leak': 60 },
            highestSeverityRegion: '19.07,72.87'
        });

        (AdaptiveWeights.prototype.adjustWeights as jest.Mock).mockReturnValue({
            duplicateThreshold: 0.75
        });

        (IntelligenceIndex.prototype.generateSnapshot as jest.Mock).mockReturnValue({
            date: '2024-05-10',
            civicIntelligenceIndex: 48,
            delta: 3,
            topEmergingConcern: 'water_leak',
            highestSeverityRegion: '19.07,72.87',
            topKeywords: ['pothole', 'leak']
        });

        engine = new PriorityEngine();
    });

    it('should run daily refinement flow sequentially', async () => {
        const snapshot = await engine.runDailyRefinement();

        // 1. TrendAnalyzer called
        expect(TrendAnalyzer.prototype.analyzeLast24h).toHaveBeenCalled();

        // 2. AdaptiveWeights called with trend results
        expect(AdaptiveWeights.prototype.adjustWeights).toHaveBeenCalledWith(
            { 'water_leak': 60 },
            '19.07,72.87'
        );

        // 3. IntelligenceIndex generated snapshot
        expect(IntelligenceIndex.prototype.generateSnapshot).toHaveBeenCalledWith(
            { 'water_leak': 60 },
            ['pothole', 'leak'],
            '19.07,72.87'
        );

        // 4. IntelligenceIndex saved snapshot
        expect(IntelligenceIndex.prototype.saveSnapshot).toHaveBeenCalledWith(snapshot);

        // Verify result
        expect(snapshot.civicIntelligenceIndex).toBe(48);
        expect(snapshot.topEmergingConcern).toBe('water_leak');
    });
});
