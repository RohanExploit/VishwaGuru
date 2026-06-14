import { PriorityEngine } from '../services/priorityEngine';
import { AdaptiveWeights } from '../services/adaptiveWeights';
import * as fs from 'fs';
import * as path from 'path';

describe('PriorityEngine Tests', () => {
  const testWeightsPath = path.join(__dirname, 'test_modelWeights_priority.json');
  let adaptiveWeights: AdaptiveWeights;
  let priorityEngine: PriorityEngine;

  beforeEach(() => {
    // Create a mock AdaptiveWeights that points to a test file
    adaptiveWeights = new AdaptiveWeights(testWeightsPath);

    // Create initial weights with some multipliers
    const initialWeights = {
      categoryWeights: {
        'Pothole': 1.5,
        'Water Supply': 2.0,
        'Garbage': 1.0,
      },
      duplicateThreshold: 0.85,
      lastUpdated: new Date().toISOString(),
      history: []
    };
    adaptiveWeights.saveWeights(initialWeights);

    // Provide the adaptive weights to priority engine
    priorityEngine = new PriorityEngine(adaptiveWeights);
  });

  afterEach(() => {
    if (fs.existsSync(testWeightsPath)) {
      fs.unlinkSync(testWeightsPath);
    }
  });

  test('should classify issue with normal severity and urgency (weight = 1)', () => {
    const result = priorityEngine.calculateSeverityAndUrgency('The garbage smells bad', 'Garbage');

    // 'smell' is a medium keyword (score: 40)
    // There are no urgency keywords, so urgency is equal to severity (40)
    expect(result.severityScore).toBe(40);
    expect(result.severity).toBe('Medium');
    expect(result.urgencyScore).toBe(40);
  });

  test('should apply category weight multiplier > 1', () => {
    const result = priorityEngine.calculateSeverityAndUrgency('The garbage smells bad', 'Pothole');

    // base score for 'smell' is 40. Pothole weight is 1.5. 40 * 1.5 = 60
    expect(result.severityScore).toBe(60);
    expect(result.severity).toBe('Medium'); // 60 is still medium (70 is high)
    expect(result.urgencyScore).toBe(60);
    expect(result.reasoning.some(r => r.includes('multiplied by 1.5'))).toBe(true);
  });

  test('should cap severity and urgency at 100 after applying multiplier', () => {
    // 'fire' is critical (score: 90)
    // 'emergency' adds 20 to urgency
    // base severity: 90, base urgency: 110 (capped to 100 before multiplier maybe?
    // Wait, the calculation says:
    //   urgency = Math.min(100, severity + urgencyWeights) -> 100
    // Then 90 * 2.0 = 180 (capped to 100)
    // Then 100 * 2.0 = 200 (capped to 100)

    const result = priorityEngine.calculateSeverityAndUrgency('Huge fire emergency in the building', 'Water Supply');

    expect(result.severityScore).toBe(100);
    expect(result.severity).toBe('Critical');
    expect(result.urgencyScore).toBe(100);
  });

  test('should change severity classification based on multiplier', () => {
    // 'garbage' is medium (score: 40)
    // category weight for 'Water Supply' is 2.0.
    // 40 * 2.0 = 80 -> should be High
    const result = priorityEngine.calculateSeverityAndUrgency('Lots of garbage here', 'Water Supply');

    expect(result.severityScore).toBe(80);
    expect(result.severity).toBe('High');
  });

  test('should suggest categories', () => {
    const result = priorityEngine.calculateSeverityAndUrgency('Huge pothole on the road', 'Pothole');
    expect(result.suggestedCategories).toContain('Pothole');
  });
});
