import { PriorityEngine } from '../services/priorityEngine';

describe('PriorityEngine', () => {
  let engine: PriorityEngine;

  beforeEach(() => {
    engine = new PriorityEngine();
  });

  it('should return base threshold of 0.85 for issues <= 100', () => {
    expect(engine.adjustDuplicateThreshold(50)).toBe(0.85);
    expect(engine.adjustDuplicateThreshold(100)).toBe(0.85);
  });

  it('should return threshold of 0.80 for issues > 100 and <= 500', () => {
    expect(engine.adjustDuplicateThreshold(150)).toBe(0.80);
    expect(engine.adjustDuplicateThreshold(500)).toBe(0.80);
  });

  it('should return threshold of 0.75 for issues > 500 and <= 1000', () => {
    expect(engine.adjustDuplicateThreshold(750)).toBe(0.75);
    expect(engine.adjustDuplicateThreshold(1000)).toBe(0.75);
  });

  it('should return threshold of 0.70 for issues > 1000', () => {
    expect(engine.adjustDuplicateThreshold(1500)).toBe(0.70);
  });
});
