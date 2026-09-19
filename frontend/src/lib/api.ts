// Client for the LOCAL FastAPI backend -- distinct from lib/supabase.ts.
// This is the one deliberate exception to "the dashboard only reads
// Supabase": a live Predict page needs a live prediction + a live Ollama
// narrative, which only the backend can provide. Every other page still
// reads exclusively from Supabase.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export interface ModelInfo {
  model_name: string;
  model_version: string;
  target: string;
  feature_columns: string[];
  categorical_domains: Record<string, string[]>;
  numeric_ranges: {
    work_year: { min: number; max: number };
    remote_ratio: { min: number; max: number; allowed_values: number[] };
  };
  metrics: { mae: number; rmse: number; r2: number };
  trained_at: string;
}

export interface PredictionInputs {
  experience_level: string;
  employment_type: string;
  job_title: string;
  employee_residence: string;
  company_location: string;
  company_size: string;
  work_year: number;
  remote_ratio: number;
}

export interface PredictResponse {
  prediction: number;
  currency: string;
  model_version: string;
  inputs: PredictionInputs;
}

export interface NarrateResponse {
  prediction: number;
  currency: string;
  model_version: string;
  headline: string;
  summary: string;
  insights: string[];
  comparison: string;
  limitations: string[];
  chart: { type: string; title: string; x: string[]; y: number[] };
  supporting_stats: Record<string, unknown>;
  percentile_rank_in_dataset: number | null;
}

export class ApiError extends Error {
  status: number;
  code: string;
  details?: unknown;

  constructor(status: number, code: string, message: string, details?: unknown) {
    super(message);
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let parsed: { error?: { code?: string; message?: string; details?: unknown } } | null = null;
    try {
      parsed = await response.json();
    } catch {
      // response body wasn't JSON -- fall through to the generic message below
    }
    const err = parsed?.error;
    throw new ApiError(response.status, err?.code ?? "UNKNOWN_ERROR", err?.message ?? response.statusText, err?.details);
  }
  return response.json() as Promise<T>;
}

function toQueryString(inputs: PredictionInputs): string {
  return new URLSearchParams({
    experience_level: inputs.experience_level,
    employment_type: inputs.employment_type,
    job_title: inputs.job_title,
    employee_residence: inputs.employee_residence,
    company_location: inputs.company_location,
    company_size: inputs.company_size,
    work_year: String(inputs.work_year),
    remote_ratio: String(inputs.remote_ratio),
  }).toString();
}

export async function fetchModelInfo(): Promise<ModelInfo> {
  const response = await fetch(`${API_BASE_URL}/model/info`);
  return handleResponse<ModelInfo>(response);
}

export async function fetchPrediction(inputs: PredictionInputs): Promise<PredictResponse> {
  const response = await fetch(`${API_BASE_URL}/predict?${toQueryString(inputs)}`);
  return handleResponse<PredictResponse>(response);
}

export async function fetchNarrative(inputs: PredictionInputs): Promise<NarrateResponse> {
  const response = await fetch(`${API_BASE_URL}/narrate?${toQueryString(inputs)}`);
  return handleResponse<NarrateResponse>(response);
}
