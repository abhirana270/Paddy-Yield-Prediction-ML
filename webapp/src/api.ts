export type Category = "Low" | "Medium" | "High";

export interface PredictInput {
  hectares: number;
  agriblock: string;
  variety: string;
  soil_type: string;
  nursery: string;
}

export interface Prediction {
  category: Category;
  confidence: number;
  probabilities: Record<Category, number>;
  estimated_yield_kg: number;
  estimated_yield_per_hectare_kg: number;
  model: string;
  out_of_training_range: boolean;
  features: Record<string, string | number>;
}

export interface Metadata {
  inputs: {
    hectares: { min: number; max: number };
    agriblock: string[];
    variety: string[];
    soil_type: string[];
    nursery: string[];
  };
  categories: { label: Category; min_kg: number; max_kg: number }[];
  feature_builder: {
    per_hectare: Record<string, number>;
    trash_per_hectare_by_variety: Record<string, number>;
    block_profiles: Record<string, Record<string, string | number>>;
  };
  metrics: {
    rows_raw: number;
    rows_after_dedup: number;
    train_rows: number;
    test_rows: number;
    feature_columns: number;
    comparison: { model: string; accuracy: number; f1_macro: number }[];
    confusion_matrix: { labels: Category[]; matrix: number[][] };
    regressor: { r2: number; mae_kg: number };
    yield_per_hectare_kg: { min: number; mean: number; max: number };
  };
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, init);
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const detail = typeof body?.detail === "string" ? body.detail : `Request failed (${res.status})`;
    throw new Error(detail);
  }
  return res.json();
}

export const getMetadata = () => request<Metadata>("/api/metadata");

export const predict = (input: PredictInput, signal?: AbortSignal) =>
  request<Prediction>("/api/predict", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
    signal,
  });
