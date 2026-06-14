import { TrendAnalyzer } from '../services/trendAnalyzer';

describe('TrendAnalyzer Unit Tests', () => {
    let analyzer: TrendAnalyzer;

    beforeEach(() => {
        analyzer = new TrendAnalyzer();
    });

    it('extractTopKeywords should ignore stop words and return top 5', () => {
        const descriptions = [
            'The pothole on Main St is huge',
            'Huge pothole near the park',
            'Water leak is causing a huge mess',
            'Another pothole, please fix the pothole',
            'Huge water leak on 5th avenue'
        ];

        const topKeywords = analyzer.extractTopKeywords(descriptions);

        // pothole (4), huge (4), water (2), leak (2), main (1)
        expect(topKeywords.length).toBeLessThanOrEqual(5);
        expect(topKeywords).toContain('pothole');
        expect(topKeywords).toContain('huge');
        expect(topKeywords).toContain('water');
        expect(topKeywords).toContain('leak');
    });

    it('detectCategorySpikes should identify >50% increase as a spike', () => {
        const olderIssues = [
            { category: 'garbage' }, { category: 'garbage' }
        ];

        const recentIssues = [
            { category: 'garbage' }, { category: 'garbage' }, { category: 'garbage' }, { category: 'garbage' }
        ];

        const spikes = analyzer.detectCategorySpikes(recentIssues, olderIssues);

        // 4 recent vs 2 older = 100% increase (spike)
        expect(spikes['garbage']).toBe(100);
    });

    it('detectCategorySpikes should catch new emerging categories with >=3 occurrences', () => {
        const olderIssues: any[] = [];
        const recentIssues = [
            { category: 'vandalism' }, { category: 'vandalism' }, { category: 'vandalism' }
        ];

        const spikes = analyzer.detectCategorySpikes(recentIssues, olderIssues);

        expect(spikes['vandalism']).toBe(100);
    });

    it('detectGeographicClustering should group by ~1km radius (2 decimal places)', () => {
        const issues = [
            { latitude: 19.07, longitude: 72.87 }, // ~1km close
            { latitude: 19.07, longitude: 72.87 },
            { latitude: 19.07, longitude: 72.87 }, // Cluster formed (3 items)
            { latitude: 18.52, longitude: 73.85 }, // Separate region
        ];

        const highestRegion = analyzer.detectGeographicClustering(issues);
        expect(highestRegion).toBe('19.07,72.87');
    });
});
