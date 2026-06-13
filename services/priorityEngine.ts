import { Issue, ModelWeights } from './types';
import { AdaptiveWeights } from './adaptiveWeights';

export class PriorityEngine {
  private adaptiveWeights: AdaptiveWeights;

  constructor(adaptiveWeights?: AdaptiveWeights) {
    this.adaptiveWeights = adaptiveWeights || new AdaptiveWeights();
  }

  public calculatePriority(issue: Issue): { severity: string; severityScore: number; urgencyScore: number; reasoning: string[] } {
    let severityScore = 0;
    let urgencyScore = 0;
    const reasoning: string[] = [];
    const text = (issue.description || "").toLowerCase();

    // 1. Calculate Base Severity based on keywords
    const criticalKeywords = ['emergency', 'accident', 'danger', 'fatal', 'immediate', 'severe'];
    const highKeywords = ['traffic', 'blocked', 'pollution', 'broken', 'smell'];
    const mediumKeywords = ['maintenance', 'crack', 'dirty'];

    let baseLabel = "Low";

    if (criticalKeywords.some(word => text.includes(word))) {
      severityScore = 90;
      baseLabel = "Critical";
      reasoning.push("Flagged as Critical due to critical keywords in description.");
    } else if (highKeywords.some(word => text.includes(word))) {
      severityScore = 70;
      baseLabel = "High";
      reasoning.push("Flagged as High Severity due to high keywords in description.");
    } else if (mediumKeywords.some(word => text.includes(word))) {
      severityScore = 40;
      baseLabel = "Medium";
      reasoning.push("Flagged as Medium Severity due to medium keywords in description.");
    } else {
      severityScore = 10;
      reasoning.push("Classified as Low Severity (maintenance/cosmetic issue).");
    }

    // 2. Apply Adaptive Category Weights
    const currentWeights = this.adaptiveWeights.loadWeights();
    const categoryWeight = currentWeights.categoryWeights[issue.category];

    // The baseline category weight is 1. If it's > 1, apply multiplier.
    if (categoryWeight !== undefined && categoryWeight > 1) {
      const oldScore = severityScore;
      severityScore = Math.min(100, Math.round(severityScore * (1 + (categoryWeight / 10))));

      if (severityScore > oldScore) {
          reasoning.push(`Severity score boosted based on historical trends for category: ${issue.category} (weight: ${categoryWeight}).`);
      }
    }

    // 3. Determine Final Label
    let severityLabel = "Low";
    if (severityScore >= 90) severityLabel = "Critical";
    else if (severityScore >= 70) severityLabel = "High";
    else if (severityScore >= 40) severityLabel = "Medium";

    // 4. Calculate Urgency (based on severity + upvotes)
    urgencyScore = severityScore;
    if (issue.upvotes && issue.upvotes > 0) {
      urgencyScore += Math.min(20, issue.upvotes * 2); // Cap upvote boost at 20
      reasoning.push(`Urgency increased by upvotes (${issue.upvotes}).`);
    }

    urgencyScore = Math.min(100, urgencyScore);

    return {
      severity: severityLabel,
      severityScore,
      urgencyScore,
      reasoning
    };
  }
}
