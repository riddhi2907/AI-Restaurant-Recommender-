import type { PreferencesFormValues } from "@/types/preferences";
import type { RecommendationResponse } from "@/types/recommendation";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export class ApiClientError extends Error {
  suggestions: string[];

  constructor(message: string, suggestions: string[] = []) {
    super(message);
    this.name = "ApiClientError";
    this.suggestions = suggestions;
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (response.ok) {
    return response.json() as Promise<T>;
  }

  let message = `Request failed (${response.status})`;
  let suggestions: string[] = [];

  try {
    const body = await response.json();
    if (typeof body.detail === "string") {
      message = body.detail;
    } else if (body.detail && typeof body.detail === "object") {
      message = body.detail.message ?? message;
      suggestions = body.detail.suggestions ?? [];
    }
  } catch {
    // ignore parse errors
  }

  throw new ApiClientError(message, suggestions);
}

export async function getHealth(): Promise<{ status: string }> {
  const response = await fetch(`${API_BASE}/health`);
  return handleResponse(response);
}

export async function getReady(): Promise<{
  status: string;
  dataset_loaded: boolean;
  groq_configured: boolean;
  warnings: string[];
}> {
  const response = await fetch(`${API_BASE}/ready`);
  return handleResponse(response);
}

export async function getLocations(): Promise<string[]> {
  const response = await fetch(`${API_BASE}/api/locations`);
  return handleResponse(response);
}

export async function getCuisines(): Promise<string[]> {
  const response = await fetch(`${API_BASE}/api/cuisines`);
  return handleResponse(response);
}

export async function postRecommendations(
  preferences: PreferencesFormValues,
): Promise<RecommendationResponse> {
  const additional = preferences.additional
    ? preferences.additional
        .split(/[,;]/)
        .map((s) => s.trim())
        .filter(Boolean)
    : [];

  const response = await fetch(`${API_BASE}/api/recommendations`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      location: preferences.location,
      budget: preferences.budget,
      cuisine: preferences.cuisine || null,
      min_rating: preferences.min_rating,
      additional,
      top_k: preferences.top_k,
    }),
  });

  return handleResponse(response);
}
