export interface Issue {
  id: number;
  reference_id?: string;
  description: string;
  category: string;
  image_path?: string;
  source?: string;
  status: string;
  created_at: string;
  verified_at?: string;
  assigned_at?: string;
  resolved_at?: string;
  user_email?: string;
  assigned_to?: string;
  upvotes: number;
  latitude?: number;
  longitude?: number;
}

export interface ModelWeights {
  categoryWeights: Record<string, number>;
  duplicateThreshold: number;
  lastUpdated: string;
  history: Array<{
    date: string;
    categoryWeights: Record<string, number>;
    duplicateThreshold: number;
  }>;
}

export interface DailySnapshot {
  date: string;
  indexScore: number;
  delta: number;
  topKeywords: string[];
  emergingConcerns: Array<{ category: string; increasePercentage: number }>;
  highestSeverityRegion?: {
    latitude: number;
    longitude: number;
    count: number;
  };
}
