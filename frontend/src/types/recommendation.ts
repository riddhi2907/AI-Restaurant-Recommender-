export interface Recommendation {
  rank: number;
  name: string;
  cuisine: string;
  rating: number;
  estimated_cost: string;
  explanation: string;
  restaurant_id?: string | null;
}

export interface RecommendationMetadata {
  total_candidates: number;
  filters_applied: Record<string, unknown>;
  llm_used: boolean;
  filters_relaxed?: string[];
  llm_latency_ms?: number | null;
  token_usage?: Record<string, number> | null;
}

export interface RecommendationResponse {
  summary: string | null;
  recommendations: Recommendation[];
  metadata: RecommendationMetadata;
}

export interface ApiErrorBody {
  detail?: string | { message?: string; suggestions?: string[] };
}
