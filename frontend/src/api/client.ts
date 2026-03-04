import type { AnalysisResult, ErrorResponse, OperationalRecord } from "./types";
import { ApiError } from "./types";

const BASE_URL: string = import.meta.env.VITE_API_BASE_URL || "/api";

async function handleResponse<T>(response: Response): Promise<T> {
  if (response.ok) {
    return response.json() as Promise<T>;
  }

  if (response.status === 413) {
    let detail: string | undefined;
    try {
      const body = (await response.json()) as { detail?: string };
      detail = body.detail;
    } catch {
      // ignore parse errors
    }
    throw new ApiError(
      detail ?? "Request entity too large",
      response.status,
      detail,
      undefined,
    );
  }

  if (response.status === 422) {
    let errors: ErrorResponse["errors"] | undefined;
    try {
      const body = (await response.json()) as ErrorResponse;
      errors = body.errors;
    } catch {
      // ignore parse errors
    }
    throw new ApiError(
      "Validation error",
      response.status,
      undefined,
      errors,
    );
  }

  // Generic non-2xx error
  let detail: string | undefined;
  try {
    const body = (await response.json()) as { detail?: string };
    detail = body.detail;
  } catch {
    // ignore parse errors
  }
  throw new ApiError(
    detail ?? `HTTP error ${response.status}`,
    response.status,
    detail,
    undefined,
  );
}

export async function fetchRecords(
  limit?: number,
  offset?: number,
): Promise<OperationalRecord[]> {
  const params = new URLSearchParams();
  if (limit !== undefined) params.set("limit", String(limit));
  if (offset !== undefined) params.set("offset", String(offset));

  const query = params.toString();
  const url = `${BASE_URL}/records${query ? `?${query}` : ""}`;

  let response: Response;
  try {
    response = await fetch(url);
  } catch (err) {
    throw new ApiError(
      err instanceof Error ? err.message : "Network error",
      0,
    );
  }

  return handleResponse<OperationalRecord[]>(response);
}

export async function uploadCSV(file: File): Promise<OperationalRecord[]> {
  const formData = new FormData();
  formData.append("file", file);

  let response: Response;
  try {
    response = await fetch(`${BASE_URL}/upload/csv`, {
      method: "POST",
      body: formData,
    });
  } catch (err) {
    throw new ApiError(
      err instanceof Error ? err.message : "Network error",
      0,
    );
  }

  return handleResponse<OperationalRecord[]>(response);
}

export async function fetchAnalysisResults(): Promise<AnalysisResult[]> {
  let response: Response;
  try {
    response = await fetch(`${BASE_URL}/analyse`);
  } catch (err) {
    throw new ApiError(
      err instanceof Error ? err.message : "Network error",
      0,
    );
  }

  return handleResponse<AnalysisResult[]>(response);
}

export async function triggerAnalysis(): Promise<AnalysisResult[]> {
  let response: Response;
  try {
    response = await fetch(`${BASE_URL}/analyse`, {
      method: "POST",
    });
  } catch (err) {
    throw new ApiError(
      err instanceof Error ? err.message : "Network error",
      0,
    );
  }

  return handleResponse<AnalysisResult[]>(response);
}

export async function healthCheck(): Promise<{ status: string }> {
  let response: Response;
  try {
    response = await fetch(`${BASE_URL}/health`);
  } catch (err) {
    throw new ApiError(
      err instanceof Error ? err.message : "Network error",
      0,
    );
  }

  return handleResponse<{ status: string }>(response);
}
