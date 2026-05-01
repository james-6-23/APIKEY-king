export type KeyType = "modelscope" | "siliconflow" | "deepseek";

export interface ApiKey {
  key: string;
  type: KeyType | string;
  source?: string;
  url?: string;
  found_at?: string;
  validation_status?: string;
  balance?: string;
}

export interface ApiKeysResponse {
  status: string;
  keys: ApiKey[];
  total: number;
  message?: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface FirstRunResponse {
  is_first_run: boolean;
}

export interface ScanStats {
  total_files: number;
  total_keys: number;
  valid_keys: number;
  last_update: string | null;
  current_query: string;
  current_query_index: number;
  total_queries: number;
  progress_percent: number;
  queries_completed: number;
  initial_unprocessed_queries: number;
  remaining_queries: number;
}

export interface ScanStatusResponse {
  status: "ok";
  running: boolean;
  paused: boolean;
  scan_mode: string | null;
  stats: ScanStats;
}

export type ScanAction = "start" | "stop" | "pause" | "resume";

export interface ValidatorConfig {
  enabled: boolean;
  model?: string | null;
}

export interface PerformanceConfig {
  max_concurrent_files: number;
  request_delay: number;
  github_timeout: number;
  validation_timeout: number;
  max_retries: number;
}

export type ScanMode =
  | "compatible"
  | "modelscope-only"
  | "siliconflow-only"
  | "deepseek-only";

export interface AppConfig {
  github_tokens: string[];
  proxy?: string | null;
  scan_mode: ScanMode | string;
  date_range_days: number;
  validators?: Record<string, ValidatorConfig>;
  performance?: PerformanceConfig;
}

export interface ConfigResponse {
  status: "ok" | "empty";
  config: AppConfig | null;
}

export interface ScanReport {
  id: number;
  scan_mode: string;
  start_time: string;
  end_time: string;
  total_files: number;
  total_keys: number;
  valid_keys: number;
  queries_processed: number;
  duration_seconds: number;
  started_at?: string;
  ended_at?: string;
}

export interface ReportsResponse {
  status: "ok";
  reports: ScanReport[];
  total: number;
}

export interface ReportKeysResponse {
  status: "ok";
  keys: string[];
  total: number;
}

export interface MemoryStats {
  processed_queries?: number;
  scanned_files?: number;
  last_scan_time?: string;
  [k: string]: unknown;
}

export interface MemoryStatsResponse {
  status: "ok";
  stats: MemoryStats;
}

export interface QueriesResponse {
  queries: string[];
  total: number;
  file: string;
}
