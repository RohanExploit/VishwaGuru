import { IntelligenceIndex } from '../services/intelligenceIndex';
import * as fs from 'fs';
import * as path from 'path';

describe('IntelligenceIndex', () => {
  const testDir = path.join(__dirname, 'testData_intelligence');
  const historyFile = path.join(testDir, 'intelligenceHistory.json');

  beforeEach(() => {
    if (fs.existsSync(testDir)) {
      fs.rmSync(testDir, { recursive: true, force: true });
    }
  });

  afterAll(() => {
    if (fs.existsSync(testDir)) {
      fs.rmSync(testDir, { recursive: true, force: true });
    }
  });

  it('should calculate initial index properly', () => {
    const indexer = new IntelligenceIndex('tests/testData_intelligence/intelligenceHistory.json');
    const result = indexer.calculateDailyIndex(100, ['road'], { 'pothole': 10 }, ['Mumbai']);
    
    expect(result.index).toBe(50.0); // Base 50, no mod for 100 issues
    expect(result.diff).toBe(0.0);
    expect(result.topConcern).toBe('pothole');
    expect(result.highestSeverityRegion).toBe('Mumbai');
    expect(fs.existsSync(historyFile)).toBeTruthy();
  });

  it('should increase score for low issue count (< 50)', () => {
    const indexer = new IntelligenceIndex('tests/testData_intelligence/intelligenceHistory.json');
    const result = indexer.calculateDailyIndex(30, [], {}, []);
    
    expect(result.index).toBe(55.0);
    expect(result.diff).toBe(5.0);
    expect(result.topConcern).toBe('None');
    expect(result.highestSeverityRegion).toBe('Unknown');
  });

  it('should decrease score for high issue count (> 200)', () => {
    const indexer = new IntelligenceIndex('tests/testData_intelligence/intelligenceHistory.json');
    const result = indexer.calculateDailyIndex(250, [], {}, []);
    
    expect(result.index).toBe(40.0);
    expect(result.diff).toBe(-10.0);
  });

  it('should not change score for exactly 50 issues', () => {
    const indexer = new IntelligenceIndex('tests/testData_intelligence/intelligenceHistory.json');
    const result = indexer.calculateDailyIndex(50, [], {}, []);
    
    expect(result.index).toBe(50.0);
    expect(result.diff).toBe(0.0);
  });

  it('should not change score for exactly 200 issues', () => {
    const indexer = new IntelligenceIndex('tests/testData_intelligence/intelligenceHistory.json');
    const result = indexer.calculateDailyIndex(200, [], {}, []);
    
    expect(result.index).toBe(50.0);
    expect(result.diff).toBe(0.0);
  });

  it('should use top keyword if category spike top concern is unknown', () => {
    const indexer = new IntelligenceIndex('tests/testData_intelligence/intelligenceHistory.json');
    const result = indexer.calculateDailyIndex(100, ['flooding'], { 'unknown': 20 }, []);
    
    expect(result.topConcern).toBe('flooding');
  });

  it('should correctly read previous history', () => {
    fs.mkdirSync(testDir, { recursive: true });
    fs.writeFileSync(historyFile, JSON.stringify([{ date: '2026-07-25', index: 60.0 }]));

    const indexer = new IntelligenceIndex('tests/testData_intelligence/intelligenceHistory.json');
    const result = indexer.calculateDailyIndex(30, [], {}, []);
    
    expect(result.index).toBe(65.0); // 60 + 5
    expect(result.diff).toBe(5.0);
  });
});
