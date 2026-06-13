import { PriorityEngine } from '../services/priorityEngine';
import { AdaptiveWeights } from '../services/adaptiveWeights';
import { Issue, ModelWeights } from '../services/types';

describe('PriorityEngine Tests', () => {
  let adaptiveWeights: AdaptiveWeights;
  let priorityEngine: PriorityEngine;

  beforeEach(() => {
    // Create mock AdaptiveWeights
    adaptiveWeights = {
      loadWeights: jest.fn().mockReturnValue({
        categoryWeights: {
          'Pothole': 5,
          'Garbage': 3,
          'Water Supply': 4,
          'Streetlight': 1, // baseline
          'Flooding': 8
        },
        duplicateThreshold: 0.85,
        lastUpdated: new Date().toISOString(),
        history: []
      } as ModelWeights),
      optimizeWeights: jest.fn(),
      saveWeights: jest.fn()
    } as any;

    priorityEngine = new PriorityEngine(adaptiveWeights);
  });

  test('should classify low severity properly', () => {
    const issue: Issue = {
      id: 1,
      description: 'The street sign is slightly tilted.',
      category: 'Streetlight',
      status: 'open',
      created_at: new Date().toISOString(),
      upvotes: 0
    };

    const result = priorityEngine.calculatePriority(issue);

    // Streetlight has weight 1, so the > 1 condition in priorityEngine.ts
    // won't apply the multiplier. Score remains 10.
    expect(result.severityScore).toBe(10);
    expect(result.severity).toBe('Low');
    expect(result.urgencyScore).toBe(10);
    expect(result.reasoning).toContain('Classified as Low Severity (maintenance/cosmetic issue).');
  });

  test('should classify high severity and apply category multiplier', () => {
    const issue: Issue = {
      id: 2,
      description: 'Broken pipe causing huge water supply problem in neighborhood.',
      category: 'Water Supply', // Weight 4
      status: 'open',
      created_at: new Date().toISOString(),
      upvotes: 5
    };

    const result = priorityEngine.calculatePriority(issue);

    // High keyword "broken" -> Base score 70.
    // Water Supply weight is 4 -> 70 * (1 + 4/10) = 70 * 1.4 = 98
    expect(result.severityScore).toBe(98);
    expect(result.severity).toBe('Critical'); // Bumped from High to Critical
    expect(result.urgencyScore).toBe(100); // 98 + 10 (upvotes) = 108 -> capped at 100

    expect(result.reasoning).toContain('Flagged as High Severity due to high keywords in description.');
    expect(result.reasoning).toContain('Severity score boosted based on historical trends for category: Water Supply (weight: 4).');
    expect(result.reasoning).toContain('Urgency increased by upvotes (5).');
  });

  test('should handle critical keywords', () => {
    const issue: Issue = {
      id: 3,
      description: 'Accident due to open manhole, severe injuries.',
      category: 'Accident', // Unknown category, defaults to 1 multiplier
      status: 'open',
      created_at: new Date().toISOString(),
      upvotes: 2
    };

    const result = priorityEngine.calculatePriority(issue);

    // Critical keyword "accident", "severe" -> Base score 90.
    // Category not defined -> Weight is undefined -> No boost.
    expect(result.severityScore).toBe(90);
    expect(result.severity).toBe('Critical');
    expect(result.urgencyScore).toBe(94); // 90 + 4 (upvotes) = 94

    expect(result.reasoning).toContain('Flagged as Critical due to critical keywords in description.');
  });
});