import {
  AnswerResponse,
  ConfigResponse,
  MeResponse,
  ProgressResponse,
  SessionListItem,
  ShareResponse,
  StartResponse,
  SummaryResponse,
} from "./types";

const API_BASE = "/api";

/** Uniform API error carrying the server's { error } message. */
export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function readCookie(name: string): string | null {
  const match = document.cookie
    .split(";")
    .map((entry) => entry.trim())
    .find((entry) => entry.startsWith(`${name}=`));
  return match ? decodeURIComponent(match.substring(name.length + 1)) : null;
}

/** Echo the CSRF cookie back as a header on mutating requests. */
function csrfHeaders(): Record<string, string> {
  const token = readCookie("XSRF-TOKEN");
  return token ? { "X-XSRF-TOKEN": token } : {};
}

async function parseResponse<T>(res: Response): Promise<T> {
  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    const message =
      (data as Record<string, unknown>)?.error ||
      (data as Record<string, unknown>)?.detail ||
      `Request failed with status ${res.status}`;
    throw new ApiError(res.status, String(message));
  }

  return data as T;
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    credentials: "same-origin",
    ...options,
    headers: {
      ...(options.headers as Record<string, string> | undefined),
      ...csrfHeaders(),
    },
  });
  return parseResponse<T>(res);
}

// ---- public / config ----

export function getConfig(): Promise<ConfigResponse> {
  return request<ConfigResponse>("/config");
}

export function getSummary(sessionId: string): Promise<SummaryResponse> {
  return request<SummaryResponse>(`/session/${sessionId}/summary`);
}

export function getSharedSummary(token: string): Promise<SummaryResponse> {
  return request<SummaryResponse>(`/share/${token}`);
}

// ---- auth ----

export function register(
  username: string,
  password: string
): Promise<{ username: string }> {
  return request("/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
}

export function login(
  username: string,
  password: string
): Promise<{ username: string }> {
  return request("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
}

export function logout(): Promise<{ ok: boolean }> {
  return request("/auth/logout", { method: "POST" });
}

export function me(): Promise<MeResponse> {
  return request<MeResponse>("/auth/me");
}

// ---- profile / interview flow ----

export async function createProfile(
  payload: FormData | Record<string, unknown>
): Promise<{ profile_id: string; resume_json: unknown }> {
  const options: RequestInit =
    payload instanceof FormData
      ? { method: "POST", body: payload }
      : {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        };

  return request("/profile", options);
}

export function startInterview(
  payload: Record<string, unknown>
): Promise<StartResponse> {
  return request<StartResponse>("/start", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function submitAnswer(
  sessionId: string,
  payload: FormData
): Promise<AnswerResponse> {
  return request<AnswerResponse>(`/answer/${sessionId}`, {
    method: "POST",
    body: payload,
  });
}

export function finishSession(sessionId: string): Promise<SummaryResponse> {
  return request<SummaryResponse>(`/session/${sessionId}/finish`, {
    method: "POST",
  });
}

// ---- history / progress / sharing / reports ----

export function getSessions(): Promise<SessionListItem[]> {
  return request<SessionListItem[]>("/sessions");
}

export function getProgress(): Promise<ProgressResponse> {
  return request<ProgressResponse>("/progress");
}

export function createShare(sessionId: string): Promise<ShareResponse> {
  return request<ShareResponse>(`/session/${sessionId}/share`, {
    method: "POST",
  });
}

export function reportUrl(sessionId: string): string {
  return `${API_BASE}/session/${sessionId}/report.pdf`;
}
