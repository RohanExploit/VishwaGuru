import { AdaptiveWeights } from '../services/adaptiveWeights';
import * as fs from 'fs';
import * as path from 'path';

describe('AdaptiveWeights', () => {
  const testDir = path.join(__dirname, 'testData_adaptive');
  const weightsFile = path.join(testDir, 'modelWeights.json');

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

  it('should initialize with default weights if file does not exist', () => {
    const adaptive = new AdaptiveWeights('tests/testData_adaptive/modelWeights.json');
    const newWeights = adaptive.optimizeWeights({}, 0);
    expect(newWeights).toEqual({ default: 1.0 });
    expect(fs.existsSync(weightsFile)).toBeTruthy();
  });

  it('should boost category weight if it represents > 10% of total volume', () => {
    const adaptive = new AdaptiveWeights('tests/testData_adaptive/modelWeights.json');
    const newWeights = adaptive.optimizeWeights({ 'pothole': 20, 'water': 5 }, 100);
    
    expect(newWeights['pothole']).toBe(1.1); // > 10%
    expect(newWeights['water']).toBeUndefined(); // <= 10%
  });
  
  it('should read existing weights from file', () => {
    fs.mkdirSync(testDir, { recursive: true });
    fs.writeFileSync(weightsFile, JSON.stringify({ current: { 'pothole': 1.5 }, history: [] }));
    
    const adaptive = new AdaptiveWeights('tests/testData_adaptive/modelWeights.json');
    const newWeights = adaptive.optimizeWeights({ 'pothole': 15 }, 100); // 15% -> boost by 0.1
    
    expect(newWeights['pothole']).toBe(1.6);
  });
});
