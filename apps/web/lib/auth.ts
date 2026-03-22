// Use empty string in browser so calls go to /api/... (proxied by Next.js)
// Use full URL on server-side (SSR/middleware)
const API_URL = typeof window !== "undefined" ? "" : (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000");

// ─── Token Management ────────────────────────────────────────────────────────

const TOKEN_KEY = "melodio_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
  document.cookie = `melodio_token=${token}; path=/; max-age=2592000; SameSite=Lax`;
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
  document.cookie = "melodio_token=; path=/; max-age=0";
}

export function isAuthenticated(): boolean {
  return !!getToken();
}

// ─── Auth API ────────────────────────────────────────────────────────────────

export interface AuthUser {
  id: string;
  email: string;
  role: string;
}

interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

/** POST /api/v1/auth/token — OAuth2 form-encoded login */
export async function login(
  email: string,
  password: string
): Promise<{ success: true; token: string } | { success: false; error: string }> {
  try {
    const body = new URLSearchParams();
    body.append("username", email);
    body.append("password", password);

    const res = await fetch(`${API_URL}/api/v1/auth/token`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: body.toString(),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      return { success: false, error: err.detail || "Invalid email or password" };
    }

    const data: TokenResponse = await res.json();
    setToken(data.access_token);
    return { success: true, token: data.access_token };
  } catch {
    return { success: false, error: "Connection error. Please try again." };
  }
}

/** POST /api/v1/auth/register */
export async function register(
  email: string,
  password: string,
  role: string
): Promise<{ success: true; token: string } | { success: false; error: string }> {
  try {
    const res = await fetch(`${API_URL}/api/v1/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password, role }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      return { success: false, error: err.detail || "Could not create account" };
    }

    const data: TokenResponse = await res.json();
    setToken(data.access_token);
    return { success: true, token: data.access_token };
  } catch {
    return { success: false, error: "Connection error. Please try again." };
  }
}

/** GET /api/v1/auth/me */
export async function getMe(token?: string): Promise<AuthUser | null> {
  try {
    const t = token || getToken();
    if (!t) return null;

    const res = await fetch(`${API_URL}/api/v1/auth/me`, {
      headers: { Authorization: `Bearer ${t}` },
    });

    if (!res.ok) {
      if (res.status === 401) clearToken();
      return null;
    }

    return res.json();
  } catch {
    return null;
  }
}

/** POST /api/v1/auth/logout */
export function logout(): void {
  clearToken();
}
