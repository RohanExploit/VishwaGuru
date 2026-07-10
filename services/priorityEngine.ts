export class PriorityEngine {
  public adjustDuplicateThreshold(totalIssues: number): number {
    let baseThreshold = 0.85; // 85% similarity

    // If there's a huge spike in issues, we loosen the threshold
    // so we catch more duplicates faster (to group mass-reports)
    if (totalIssues > 1000) {
      baseThreshold = 0.70;
    } else if (totalIssues > 500) {
      baseThreshold = 0.75;
    } else if (totalIssues > 100) {
      baseThreshold = 0.80;
    }

    return baseThreshold;
  }
}
