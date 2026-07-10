import sqlite3 from 'sqlite3';

export class TrendAnalyzer {
  private db: sqlite3.Database;

  constructor(dbPath: string = 'backend/data/issues.db') {
    this.db = new sqlite3.Database(dbPath);
  }

  public async analyzeLast24Hours(): Promise<{
    topKeywords: string[],
    categorySpikes: Record<string, number>,
    locations: string[],
    totalIssues: number
  }> {
    return new Promise((resolve, reject) => {
      const yesterday = new Date();
      yesterday.setDate(yesterday.getDate() - 1);
      const yesterdayIso = yesterday.toISOString();

      this.db.all(
        `SELECT description, category, location FROM issues WHERE created_at >= ?`,
        [yesterdayIso],
        (err, rows: any[]) => {
          if (err) return reject(err);

          const keywordsMap: Record<string, number> = {};
          const categorySpikes: Record<string, number> = {};
          const locationsSet = new Set<string>();
          let totalIssues = 0;

          // Simple stop words
          const stopWords = new Set(['the', 'and', 'to', 'a', 'of', 'in', 'is', 'for', 'that', 'on', 'with', 'as', 'at', 'this', 'it', 'from']);

          rows.forEach(row => {
            totalIssues++;

            // Count categories
            const cat = row.category || 'unknown';
            categorySpikes[cat] = (categorySpikes[cat] || 0) + 1;

            // Collect locations
            if (row.location) {
              locationsSet.add(row.location);
            }

            // Extract basic keywords from description
            if (row.description) {
              const words = row.description.toLowerCase().match(/\b(\w+)\b/g);
              if (words) {
                words.forEach((word: string) => {
                  if (word.length > 3 && !stopWords.has(word)) {
                    keywordsMap[word] = (keywordsMap[word] || 0) + 1;
                  }
                });
              }
            }
          });

          // Top 5 keywords
          const topKeywords = Object.entries(keywordsMap)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 5)
            .map(entry => entry[0]);

          resolve({
            topKeywords,
            categorySpikes,
            locations: Array.from(locationsSet),
            totalIssues
          });
        }
      );
    });
  }

  public close() {
    this.db.close();
  }
}
