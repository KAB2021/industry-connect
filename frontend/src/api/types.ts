export interface OperationalRecord {
  id: string;
  source: string;
  timestamp: string;
  entity_id: string;
  metric_name: string;
  metric_value: number;
  analysed: boolean;
  ingested_at: string;
}

export interface Anomaly {
  record_id: string;
  metric_name: string;
  metric_value: number;
  explanation: string;
}

export interface AnalysisResult {
  id: string;
  record_ids: string[];
  summary: string;
  anomalies: Anomaly[];
  prompt: string;
  response_raw: string;
  prompt_tokens: number | null;
  completion_tokens: number | null;
  created_at: string;
}

export interface CSVRowError {
  row: number;
  field: string;
  message: string;
}

export interface ErrorResponse {
  errors: CSVRowError[];
}

export class ApiError extends Error {
  status: number;
  detail?: string;
  errors?: CSVRowError[];

  constructor(
    message: string,
    status: number,
    detail?: string,
    errors?: CSVRowError[],
  ) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
    this.errors = errors;
  }
}
