import { Issue } from "./types";

export class TrendAnalyzer {
  public getTopKeywords(issues: Issue[], limit: number = 5): string[] {
    const wordCounts: Record<string, number> = {};
    const stopWords = new Set([
      "the",
      "is",
      "in",
      "at",
      "of",
      "on",
      "and",
      "a",
      "to",
      "for",
      "with",
      "it",
      "as",
      "by",
      "are",
      "this",
      "that",
      "from",
      "an",
      "be",
    ]);

    issues.forEach((issue) => {
      if (!issue.description) return;
      const words =
        issue.description.toLowerCase().match(/\b[a-z]{3,}\b/g) || [];
      words.forEach((word) => {
        if (!stopWords.has(word)) {
          wordCounts[word] = (wordCounts[word] || 0) + 1;
        }
      });
    });

    return Object.entries(wordCounts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, limit)
      .map((entry) => entry[0]);
  }

  public detectCategorySpikes(
    currentIssues: Issue[],
    previousIssues: Issue[],
    thresholdIncrease: number = 0.5, // 50% increase
  ): Array<{ category: string; increasePercentage: number }> {
    const currentCounts = this.getCategoryCounts(currentIssues);
    const previousCounts = this.getCategoryCounts(previousIssues);

    const spikes: Array<{ category: string; increasePercentage: number }> = [];

    for (const [category, currentCount] of Object.entries(currentCounts)) {
      const prevCount = previousCounts[category] || 0;
      if (prevCount === 0) {
        if (currentCount > 5) {
          // baseline to avoid 1 issue spike
          spikes.push({ category, increasePercentage: 100 });
        }
        continue;
      }

      const increase = (currentCount - prevCount) / prevCount;
      if (increase >= thresholdIncrease) {
        spikes.push({
          category,
          increasePercentage: Math.round(increase * 100),
        });
      }
    }

    // Sort by highest increase
    return spikes.sort((a, b) => b.increasePercentage - a.increasePercentage);
  }

  public identifyGeographicClustering(
    issues: Issue[],
  ): { latitude: number; longitude: number; count: number } | undefined {
    // Basic clustering approach: round lat/lon to ~1.1km (2 decimal places)
    const clusters: Record<
      string,
      { count: number; lat: number; lon: number }
    > = {};
    let maxCluster:
      | { latitude: number; longitude: number; count: number }
      | undefined;

    issues.forEach((issue) => {
      if (issue.latitude == null || issue.longitude == null) return;

      const roundedLat = parseFloat(issue.latitude.toFixed(2));
      const roundedLon = parseFloat(issue.longitude.toFixed(2));
      const key = `${roundedLat},${roundedLon}`;

      if (!clusters[key]) {
        clusters[key] = { count: 0, lat: roundedLat, lon: roundedLon };
      }
      clusters[key].count++;

      if (!maxCluster || clusters[key].count > maxCluster.count) {
        maxCluster = {
          latitude: clusters[key].lat,
          longitude: clusters[key].lon,
          count: clusters[key].count,
        };
      }
    });

    return maxCluster;
  }

  private getCategoryCounts(issues: Issue[]): Record<string, number> {
    const counts: Record<string, number> = {};
    issues.forEach((issue) => {
      counts[issue.category] = (counts[issue.category] || 0) + 1;
    });
    return counts;
  }
}
