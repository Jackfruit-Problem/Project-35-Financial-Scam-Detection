/**
 * One place that knows how to talk to the API.
 *
 * Every call goes through request(), so the auth header, JSON handling and
 * error shape are defined once. FastAPI returns validation errors as a list
 * of objects, which would render as "[object Object]" if passed straight to
 * the UI, so they are flattened into a sentence here.
 */

const TOKEN_KEY = "fsdiras.token";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string | null): void {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

function readDetail(detail: unknown): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item: any) => {
        const field = Array.isArray(item?.loc) ? item.loc[item.loc.length - 1] : null;
        return field ? `${field}: ${item.msg}` : item?.msg ?? "Invalid value";
      })
      .join("; ");
  }
  return "Something went wrong";
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers = new Headers(options.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (options.body && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`/api/v1${path}`, { ...options, headers });

  if (response.status === 204) return undefined as T;

  if (!response.ok) {
    let detail: unknown = null;
    try {
      detail = (await response.json())?.detail;
    } catch {
      /* a non-JSON error body is still an error */
    }
    // An expired or revoked token should not leave the app half-logged-in.
    if (response.status === 401) setToken(null);
    throw new ApiError(response.status, readDetail(detail));
  }

  const contentType = response.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) return response.json();
  return response.blob() as unknown as T;
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "POST", body: body ? JSON.stringify(body) : undefined }),
  patch: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "PATCH", body: body ? JSON.stringify(body) : undefined }),
  del: <T>(path: string) => request<T>(path, { method: "DELETE" }),
  upload: <T>(path: string, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<T>(path, { method: "POST", body: form });
  },
  /** Downloads go through fetch too, so the auth header is attached. */
  download: async (path: string, filename: string) => {
    const blob = await request<Blob>(path);
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
  },
};

// --- shapes the UI relies on ------------------------------------------------

export type Role = "victim" | "investigator" | "recovery_officer" | "admin";
export type RiskBand = "low" | "medium" | "high";

export interface User {
  id: number;
  full_name: string;
  email: string;
  role: Role;
  is_active: boolean;
}

export interface Report {
  id: number;
  report_ref: string;
  reporter_name: string;
  reporter_contact: string;
  report_date: string;
  category: string;
  description: string;
  amount_involved: number | null;
  evidence_attached: boolean;
  risk_score: number | null;
  risk_band: RiskBand | null;
  created_at: string;
}

export interface Case {
  id: number;
  case_ref: string;
  report_id: number;
  assigned_investigator_id: number | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface Detection {
  risk_score: number;
  risk_band: RiskBand;
  reasons: string[];
  matched_blacklist: boolean;
  model_version: string;
  latency_ms: number;
  advisory_note: string;
}

export interface Evidence {
  id: number;
  filename: string;
  content_type: string;
  size_bytes: number;
  sha256: string;
  is_archived: boolean;
  archive_reason: string | null;
  created_at: string;
}

export interface CustodyEvent {
  id: number;
  action: string;
  actor_id: number;
  detail: string | null;
  prev_hash: string | null;
  entry_hash: string;
  created_at: string;
}

export interface Verification {
  evidence_id: number;
  chain_intact: boolean;
  file_intact: boolean;
  broken_at_event_id: number | null;
}

export interface Recovery {
  id: number;
  case_id: number;
  bank_name: string | null;
  ifsc_code: string | null;
  account_number: string | null;
  amount_reported: number;
  amount_recovered: number;
  status: string;
  remarks: string | null;
}

export interface Article {
  id: number;
  title: string;
  category: string;
  body: string;
  is_published: boolean;
}

export interface Analytics {
  total_reports: number;
  total_cases: number;
  resolved_cases: number;
  resolution_rate: number;
  total_amount_reported: number;
  total_amount_recovered: number;
  recovery_rate: number;
  fully_recovered_cases: number;
  trending_categories: { category: string; count: number }[];
}
