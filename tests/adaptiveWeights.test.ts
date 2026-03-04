import { AdaptiveWeights } from '../services/adaptiveWeights';
import * as fs from 'fs';
import * as path from 'path';

describe('AdaptiveWeights Unit Tests', () => {
    let adaptiveWeights: AdaptiveWeights;
    const testWeightsPath = path.resolve(__dirname, '../data/test_modelWeights.json');

    beforeEach(() => {
        process.env.WEIGHTS_PATH = testWeightsPath;
        adaptiveWeights = new AdaptiveWeights();

        // Setup default weights
        if (fs.existsSync(testWeightsPath)) fs.unlinkSync(testWeightsPath);
    });

    afterAll(() => {
        if (fs.existsSync(testWeightsPath)) fs.unlinkSync(testWeightsPath);
    });

    it('should adjust category weights based on spikes', () => {
        const spikes = {
            'garbage': 60, // Moderate spike (+0.5)
            'pothole': 150 // High urgency spike (+1.5)
        };

        const result = adaptiveWeights.adjustWeights(spikes, null);

        // Default garbage: 4, POT: 5
        expect(result.severityWeights['garbage']).toBe(4.5);
        expect(result.severityWeights['pothole']).toBe(6.5);
    });

    it('should cap category weights at 10', () => {
        const spikes = { 'power_outage': 200 }; // Default 7, +1.5 = 8.5

        let result = adaptiveWeights.adjustWeights(spikes, null);
        result = adaptiveWeights.adjustWeights(spikes, null);
        result = adaptiveWeights.adjustWeights(spikes, null); // Maxed out

        expect(result.severityWeights['power_outage']).toBe(10);
    });

    it('should lower duplicateThreshold if clustering is detected', () => {
        const result = adaptiveWeights.adjustWeights({}, '19.07,72.87'); // Cluster

        // Default: 0.8, -0.05
        expect(result.duplicateThreshold).toBeCloseTo(0.75);
    });

    it('should raise duplicateThreshold if no clustering detected', () => {
        // First force it lower
        adaptiveWeights.adjustWeights({}, 'cluster');
        let lowered = adaptiveWeights.adjustWeights({}, 'cluster');

        // Then restore
        const result = adaptiveWeights.adjustWeights({}, null);
        expect(result.duplicateThreshold).toBeCloseTo(lowered.duplicateThreshold + 0.01);
    });
});
