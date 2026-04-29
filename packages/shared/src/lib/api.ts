/**
 * Minimal API client.
 *
 * BASE_URL is empty on web (Next.js uses relative paths via its own API routes).
 * On mobile (Expo), set EXPO_PUBLIC_API_URL to the full FastAPI server URL,
 * e.g. https://api.claimlense.com
 *
 * Usage:
 *   import { apiClient } from "@claimlense/shared/lib/api";
 *   const data = await apiClient.get<InsurerResponse[]>("/api/insurers");
 */

type RequestOptions = Omit<RequestInit, "body"> & {
  token?: string; // Firebase ID token — passed as Authorization: Bearer <token>
  body?: unknown;
};

function getBaseUrl(): string {
  // Web (Next.js): empty string → relative URLs → Next.js API routes handle proxying
  // Mobile (Expo): reads env var set in app.config.ts
  if (typeof process !== "undefined") {
    return (process.env as Record<string, string | undefined>)["EXPO_PUBLIC_API_URL"] ?? "";
  }
  return "";
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { token, body, ...rest } = options;

  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(rest.headers ?? {}),
  };

  const response = await fetch(`${getBaseUrl()}${path}`, {
    ...rest,
    headers,
    ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
  });

  if (!response.ok) {
    const text = await response.text().catch(() => response.statusText);
    throw new Error(`API ${response.status}: ${text}`);
  }

  // Return undefined for 204 No Content
  if (response.status === 204) return undefined as unknown as T;

  return response.json() as Promise<T>;
}

export const apiClient = {
  get: <T>(path: string, options?: RequestOptions) =>
    request<T>(path, { ...options, method: "GET" }),

  post: <T>(path: string, body: unknown, options?: RequestOptions) =>
    request<T>(path, { ...options, method: "POST", body }),

  delete: <T>(path: string, options?: RequestOptions) =>
    request<T>(path, { ...options, method: "DELETE" }),
};
