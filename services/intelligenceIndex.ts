import fs from 'fs';
import path from 'path';

export class IntelligenceIndex {
  private historyPath: string;

  constructor(historyPath: string = 'data/intelligenceHistory.json') {
    this.historyPath = path.resolve(process.cwd(), historyPath);
  }

  public calculateDailyIndex(
    totalIssues: number,
    topKeywords: string[],
    categorySpikes: Record<string, number>,
    locations: string[]
  ): { index: number, diff: number, topConcern: string, highestSeverityRegion: string } {
    let lastIndex = 50.0; // Base baseline

    if (fs.existsSync(this.historyPath)) {
      try {
         const data = fs.readFileSync(this.historyPath, 'utf8');
         const history = JSON.parse(data);
         if (history.length > 0) {
            lastIndex = history[history.length - 1].index;
         }
      } catch(err) {}
    }

    // Heuristic: lower issues + highly distributed = better score
    // Lots of issues + localized = lower score (problematic)
    let scoreMod = 0;
    if (totalIssues < 50) scoreMod += 5;
    else if (totalIssues > 200) scoreMod -= 10;

    let newIndex = parseFloat((lastIndex + scoreMod).toFixed(1));
    if (newIndex > 100) newIndex = 100;
    if (newIndex < 0) newIndex = 0;

    const diff = parseFloat((newIndex - lastIndex).toFixed(1));

    // Find top concern from categories
    let topConcern = 'None';
    let maxSpike = 0;
    for (const [cat, count] of Object.entries(categorySpikes)) {
      if (count > maxSpike) {
        maxSpike = count;
        topConcern = cat;
      }
    }

    // Top keyword fallback
    if (topConcern === 'unknown' && topKeywords.length > 0) {
       topConcern = topKeywords[0];
    }

    // Highest severity region (mock heuristic: just take first location if exists, or 'Unknown')
    const highestSeverityRegion = locations.length > 0 ? locations[0] : 'Unknown';

    // Save history
    const historyEntry = { date: new Date().toISOString(), index: newIndex };

    let currentHistory = [];
    if (fs.existsSync(this.historyPath)) {
       try {
         currentHistory = JSON.parse(fs.readFileSync(this.historyPath, 'utf8'));
       } catch(err){}
    }
    currentHistory.push(historyEntry);

    const dir = path.dirname(this.historyPath);
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, {recursive: true});

    fs.writeFileSync(this.historyPath, JSON.stringify(currentHistory, null, 2));

    return {
      index: newIndex,
      diff,
      topConcern,
      highestSeverityRegion
    };
  }
}
