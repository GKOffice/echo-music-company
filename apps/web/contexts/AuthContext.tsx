"use client";

import { createContext, useContext, useEffect, useState } from "react";
import {
  login as loginApi,
  register as registerApi,
  getMe,
  logout as logoutApi,
  getToken,
  type AuthUser,
} from "@/lib/auth";

export type User = AuthUser;

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<{ success: boolean; error?: string }>;
  signup: (email: string, password: string, role: string) => Promise<{ success: boolean; error?: string }>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // On mount: check for existing token and fetch user
  useEffect(() => {
    const token = getToken();
    if (!token) {
      setLoading(false);
      return;
    }
    getMe(token)
      .then((data) => { if (data) setUser(data); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  async function login(email: string, password: string): Promise<{ success: boolean; error?: string }> {
    const result = await loginApi(email, password);
    if (!result.success) {
      return { success: false, error: result.error };
    }
    // Fetch user profile after successful login
    const me = await getMe(result.token);
    if (me) {
      setUser(me);
    } else {
      // Fallback: we have a valid token but /me failed — set minimal user
      setUser({ id: "", email, role: "artist" });
    }
    return { success: true };
  }

  async function signup(email: string, password: string, role: string): Promise<{ success: boolean; error?: string }> {
    const result = await registerApi(email, password, role);
    if (!result.success) {
      return { success: false, error: result.error };
    }
    // Fetch user profile after successful registration
    const me = await getMe(result.token);
    if (me) {
      setUser(me);
    } else {
      setUser({ id: "", email, role });
    }
    return { success: true };
  }

  function logout() {
    logoutApi();
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
