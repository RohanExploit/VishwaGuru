/**
 * Priority Engine - Client-side version
 * A modular service for analyzing civic issues locally before submission.
 */

export interface AnalysisResult {
  severity: 'Critical' | 'High' | 'Medium' | 'Low';
  severityScore: number;
  urgencyScore: number;
  suggestedCategories: string[];
  reasoning: string[];
}

const SEVERITY_KEYWORDS = {
  critical: [
    "fire", "explosion", "blood", "death", "collapse", "gas leak",
    "electric shock", "spark", "electrocution", "drowning",
    "flood", "landslide", "earthquake", "cyclone", "hurricane",
    "attack", "assault", "rabid", "deadly", "fatal", "emergency",
    "blocked road", "ambulance", "hospital", "school", "child",
    "exposed wire", "transformer", "chemical", "toxic", "poison",
    "weapon", "gun", "bomb", "terror", "riot", "stampede",
    "structural failure", "pillar crack", "bridge crack"
  ],
  high: [
    "accident", "injury", "broken", "bleeding", "hazard", "risk",
    "dangerous", "unsafe", "threat", "pollution", "smoke",
    "sewage", "overflow", "contamination", "infection", "disease",
    "mosquito", "dengue", "malaria", "typhoid", "cholera",
    "rat", "snake", "stray dog", "bite", "attack",
    "theft", "robbery", "burglary", "harassment", "abuse",
    "illegal", "crime", "violation", "bribe", "corruption",
    "traffic jam", "congestion", "gridlock", "delay",
    "no water", "power cut", "blackout", "load shedding",
    "pothole", "manhole", "open drain", "water logging"
  ],
  medium: [
    "garbage", "trash", "waste", "litter", "rubbish", "dustbin",
    "smell", "odor", "stink", "foul", "dirty", "unclean",
    "messy", "ugly", "eyesore", "bad", "poor",
    "leak", "drip", "seepage", "moisture", "damp",
    "noise", "loud", "sound", "music", "party", "barking",
    "encroachment", "hawker", "vendor", "stall", "shop",
    "parking", "parked", "vehicle", "car", "bike", "scooter",
    "construction", "debris", "material", "sand", "cement",
    "graffiti", "poster", "banner", "hoarding", "advertisement"
  ],
  low: [
    "light", "lamp", "bulb", "flicker", "dim", "dark",
    "sign", "board", "paint", "color", "faded",
    "bench", "chair", "seat", "grass", "plant", "tree",
    "leaf", "branch", "garden", "park", "playground",
    "cosmetic", "look", "appearance", "aesthetic"
  ]
};

const URGENCY_PATTERNS = [
  { pattern: /\b(now|immediately|urgent|emergency|critical|danger|help)\b/i, weight: 20 },
  { pattern: /\b(today|tonight|morning|evening|afternoon)\b/i, weight: 10 },
  { pattern: /\b(yesterday|last night|week|month)\b/i, weight: 5 },
  { pattern: /\b(blood|bleeding|injury|hurt|pain)\b/i, weight: 25 },
  { pattern: /\b(fire|smoke|flame|burn)\b/i, weight: 30 },
  { pattern: /\b(blocked|stuck|trapped)\b/i, weight: 15 },
  { pattern: /\b(school|hospital|clinic)\b/i, weight: 15 },
  { pattern: /\b(child|kid|baby|elderly|senior)\b/i, weight: 10 }
];

const CATEGORIES: Record<string, string[]> = {
  "Fire": ["fire", "smoke", "flame", "burn", "explosion"],
  "Pothole": ["pothole", "hole", "crater", "road damage", "broken road"],
  "Street Light": ["light", "lamp", "bulb", "dark", "street light"],
  "Garbage": ["garbage", "trash", "waste", "litter", "rubbish", "dump", "dustbin"],
  "Water Leak": ["water", "leak", "pipe", "burst", "flood", "seepage"],
  "Stray Animal": ["dog", "cat", "cow", "cattle", "monkey", "bite", "stray", "animal", "rabid"],
  "Construction Safety": ["construction", "debris", "material", "cement", "sand", "building"],
  "Illegal Parking": ["parking", "parked", "blocking", "vehicle", "car", "bike"],
  "Vandalism": ["graffiti", "paint", "broken", "destroy", "damage", "poster"],
  "Infrastructure": ["bridge", "flyover", "pillar", "crack", "collapse", "structure", "manhole", "drain", "wire", "cable", "pole"],
  "Traffic Sign": ["sign", "signal", "light", "traffic", "board", "direction"],
  "Public Facilities": ["toilet", "washroom", "bench", "seat", "park", "garden", "playground"],
  "Tree Hazard": ["tree", "branch", "fallen", "root", "leaf"],
  "Accessibility": ["ramp", "wheelchair", "step", "stair", "access", "disability"],
  "Noise Pollution": ["noise", "loud", "sound", "music", "speaker"],
  "Air Pollution": ["smoke", "dust", "fume", "smell", "pollution", "air"],
  "Water Pollution": ["river", "lake", "pond", "chemical", "oil", "poison", "fish"],
  "Health Hazard": ["mosquito", "dengue", "malaria", "rat", "disease", "health"],
  "Crowd": ["crowd", "gathering", "mob", "people", "protest"],
  "Gas Leak": ["gas", "leak", "smell", "cylinder", "pipeline"],
  "Environment": ["tree", "cutting", "deforestation", "forest", "nature"]
};

export function analyzeIssue(description: string, imageLabels: string[] = []): AnalysisResult {
  const text = (description + " " + imageLabels.join(" ")).toLowerCase();

  const { severity, severityScore, reasons: severityReasons } = calculateSeverity(text);
  const { urgencyScore, reasons: urgencyReasons } = calculateUrgency(text, severityScore);
  const suggestedCategories = detectCategories(text);

  let reasoning = [...severityReasons, ...urgencyReasons];
  if (reasoning.length === 0) {
    reasoning = ["Standard priority based on general keywords."];
  }

  return {
    severity,
    severityScore,
    urgencyScore,
    suggestedCategories,
    reasoning
  };
}

function calculateSeverity(text: string) {
  let score = 0;
  let severity: AnalysisResult['severity'] = 'Low';
  const reasons: string[] = [];

  // Critical
  const criticalMatches = SEVERITY_KEYWORDS.critical.filter(k => text.includes(k));
  if (criticalMatches.length > 0) {
    score = 90;
    severity = 'Critical';
    reasons.push(`Flagged as Critical due to keywords: ${criticalMatches.slice(0, 3).join(', ')}`);
  }

  // High
  if (score < 70) {
    const highMatches = SEVERITY_KEYWORDS.high.filter(k => text.includes(k));
    if (highMatches.length > 0) {
      score = Math.max(score, 70);
      severity = (score === 70) ? 'High' : severity;
      reasons.push(`Flagged as High Severity due to keywords: ${highMatches.slice(0, 3).join(', ')}`);
    }
  }

  // Medium
  if (score < 40) {
    const mediumMatches = SEVERITY_KEYWORDS.medium.filter(k => text.includes(k));
    if (mediumMatches.length > 0) {
      score = Math.max(score, 40);
      severity = (score === 40) ? 'Medium' : severity;
      reasons.push(`Flagged as Medium Severity due to keywords: ${mediumMatches.slice(0, 3).join(', ')}`);
    }
  }

  // Low (default)
  if (score === 0) {
    score = 10;
    severity = 'Low';
    reasons.push("Classified as Low Severity (maintenance/cosmetic issue)");
  }

  return { severity, severityScore: score, reasons };
}

function calculateUrgency(text: string, severityScore: number) {
  let urgency = severityScore;
  const reasons: string[] = [];

  for (const { pattern, weight } of URGENCY_PATTERNS) {
    if (pattern.test(text)) {
      urgency += weight;
      const match = text.match(pattern);
      if (match) {
          reasons.push(`Urgency increased by context matching pattern: '${match[0]}'`);
      }
    }
  }

  return {
    urgencyScore: Math.min(100, urgency),
    reasons
  };
}

function detectCategories(text: string): string[] {
  const scores: { category: string, count: number }[] = [];

  for (const [category, keywords] of Object.entries(CATEGORIES)) {
    const count = keywords.filter(k => text.includes(k)).length;
    if (count > 0) {
      scores.push({ category, count });
    }
  }

  return scores
    .sort((a, b) => b.count - a.count)
    .slice(0, 3)
    .map(s => s.category);
}
