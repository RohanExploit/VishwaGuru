import fs from 'fs';
import path from 'path';

export class AdaptiveWeights {
  private weightsPath: string;

  constructor(weightsPath: string = 'data/modelWeights.json') {
    this.weightsPath = path.resolve(process.cwd(), weightsPath);
  }

  public optimizeWeights(categorySpikes: Record<string, number>, totalIssues: number): Record<string, number> {
    let currentWeights: { current: Record<string, number>, history: any[] } = { current: { default: 1.0 }, history: [] };

    if (fs.existsSync(this.weightsPath)) {
      try {
        const data = fs.readFileSync(this.weightsPath, 'utf8');
        currentWeights = JSON.parse(data);
      } catch (err) {
        // file unreadable or invalid json
      }
    }

    const previousWeights = { ...currentWeights.current };
    const newWeights = { ...currentWeights.current };

    if (totalIssues > 0) {
      for (const [category, count] of Object.entries(categorySpikes)) {
        const ratio = count / totalIssues;
        // Simple heuristic: if a category represents > 10% of daily volume, boost its severity weight slightly
        if (ratio > 0.1) {
           const existing = newWeights[category] || 1.0;
           newWeights[category] = parseFloat((existing + 0.1).toFixed(2));
        }
      }
    }

    currentWeights.history.push({
      date: new Date().toISOString(),
      previous: previousWeights,
      updated: newWeights
    });

    currentWeights.current = newWeights;

    // ensure dir exists
    const dir = path.dirname(this.weightsPath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }

    fs.writeFileSync(this.weightsPath, JSON.stringify(currentWeights, null, 2));

    return newWeights;
  }
}
