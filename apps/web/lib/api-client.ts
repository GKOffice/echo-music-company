import { API_URL } from "./config";
import { getToken, clearToken } from "./auth";


/**
 * Authenticated fetch wrapper.
 * Auto-attaches Authorization header and handles 401 → redirect to login.
 */
export async function apiClient<T = unknown>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    ...((options.headers as Record<string, string>) || {}),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  // Default to JSON content-type for non-GET requests without a body type set
  if (options.method && options.method !== "GET" && !headers["Content-Type"] && typeof options.body === "string") {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(`${API_URL}${path}`, { ...options, headers });

  if (res.status === 401 && typeof window !== "undefined") {
    clearToken();
    window.location.href = "/auth/login";
    throw new Error("Unauthorized");
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `API error: ${res.status}`);
  }

  return res.json();
}
