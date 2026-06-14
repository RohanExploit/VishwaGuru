import { IntelligenceIndex } from '../services/intelligenceIndex';
import * as fs from 'fs';
import * as path from 'path';

describe('IntelligenceIndex Unit Tests', () => {
    let index: IntelligenceIndex;
    const testDir = path.resolve(__dirname, '../data/test_snapshots');

    beforeEach(() => {
        process.env.SNAPSHOTS_DIR = testDir;
        index = new IntelligenceIndex();

        if (!fs.existsSync(testDir)) fs.mkdirSync(testDir, { recursive: true });

        // Clean old files
        const files = fs.readdirSync(testDir);
        for (const file of files) fs.unlinkSync(path.join(testDir, file));
    });

    afterAll(() => {
        const files = fs.readdirSync(testDir);
        for (const file of files) fs.unlinkSync(path.join(testDir, file));
        fs.rmdirSync(testDir);
    });

    it('calculateIndexScore should return base score for normal day', () => {
        const score = index.calculateIndexScore({}, 0); // No spikes, no keywords
        expect(score).toBe(50);
    });

    it('calculateIndexScore should reward high activity (keywords) without spikes', () => {
        const score = index.calculateIndexScore({}, 5); // Keywords present, 0 spikes
        expect(score).toBe(52); // +2 reward
    });

    it('calculateIndexScore should penalize spikes based on percentage', () => {
        const spikes = { 'garbage': 100, 'pothole': 50 }; // (1 * 2) + (0.5 * 2) = 3 penalty
        const score = index.calculateIndexScore(spikes, 5); // 50 - 3 = 47
        expect(score).toBe(47);
    });

    it('generateSnapshot should calculate delta against previous day', () => {
        const today = new Date();
        const yesterday = new Date(today);
        yesterday.setDate(yesterday.getDate() - 1);
        const yesterdayStr = yesterday.toISOString().split('T')[0];

        // Mock yesterday's snapshot: base score was 45
        fs.writeFileSync(path.join(testDir, `${yesterdayStr}.json`), JSON.stringify({
            date: yesterdayStr,
            civicIntelligenceIndex: 45
        }));

        const snapshot = index.generateSnapshot({}, [], null);

        // Today is normal (50 score)
        expect(snapshot.civicIntelligenceIndex).toBe(50);
        expect(snapshot.delta).toBe(5); // 50 - 45
    });

    it('generateSnapshot should identify top emerging concern', () => {
        const spikes = { 'vandalism': 50, 'power_outage': 150 };

        const snapshot = index.generateSnapshot(spikes, [], null);

        expect(snapshot.topEmergingConcern).toBe('power_outage');
    });
});
