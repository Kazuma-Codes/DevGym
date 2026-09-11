import {
  AnswerResponse,
  StartResponse,
  SummaryResponse,
} from "./types";

const API_BASE = "/api";

async function parseResponse<T>(res: Response): Promise<T> {
  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    const message =
      (data as any)?.detail ||
      `Request failed with status ${res.status}`;

    throw new Error(message);
  }

  return data as T;
}

export async function createProfile(
  payload: FormData | Record<string, unknown>
): Promise<{ profile_id: string; resume_json: any }> {
  const options: RequestInit =
    payload instanceof FormData
      ? {
          method: "POST",
          body: payload,
        }
      : {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(payload),
        };

  const res = await fetch(`${API_BASE}/profile`, options);
  return parseResponse(res);
}

export async function startInterview(
  payload: Record<string, unknown>
): Promise<StartResponse> {
  const res = await fetch(`${API_BASE}/start`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  return parseResponse<StartResponse>(res);
}

export async function submitAnswer(
  sessionId: string,
  payload: FormData
): Promise<AnswerResponse> {
  const res = await fetch(`${API_BASE}/answer/${sessionId}`, {
    method: "POST",
    body: payload,
  });

  return parseResponse<AnswerResponse>(res);
}

export async function finishSession(
  sessionId: string
): Promise<SummaryResponse> {
  const res = await fetch(`${API_BASE}/session/${sessionId}/finish`, {
    method: "POST",
  });

  return parseResponse<SummaryResponse>(res);
}

export async function getSummary(
  sessionId: string
): Promise<SummaryResponse> {
  const res = await fetch(`${API_BASE}/session/${sessionId}/summary`);
  return parseResponse<SummaryResponse>(res);
}