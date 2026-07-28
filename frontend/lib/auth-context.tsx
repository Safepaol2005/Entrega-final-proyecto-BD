"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import {
  api,
  clearAuth,
  getStoredToken,
  getStoredUser,
  persistAuth,
} from "@/lib/api";
import type { AuthResponse, UserPublic, UserRole } from "@/lib/types";

type AuthContextValue = {
  user: UserPublic | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (payload: {
    nombre_completo: string;
    correo_estudiantil: string;
    password: string;
    roles: UserRole[];
  }) => Promise<void>;
  logout: () => void;
  refreshMe: () => Promise<void>;
  hasRole: (role: UserRole) => boolean;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserPublic | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const t = getStoredToken();
    const u = getStoredUser();
    setToken(t);
    setUser(u);
    setLoading(false);
  }, []);

  const applyAuth = useCallback((auth: AuthResponse) => {
    persistAuth(auth);
    setToken(auth.token.access_token);
    setUser(auth.user);
  }, []);

  const login = useCallback(
    async (email: string, password: string) => {
      const auth = await api.login({
        correo_estudiantil: email,
        password,
      });
      applyAuth(auth);
    },
    [applyAuth],
  );

  const register = useCallback(
    async (payload: {
      nombre_completo: string;
      correo_estudiantil: string;
      password: string;
      roles: UserRole[];
    }) => {
      const auth = await api.register(payload);
      applyAuth(auth);
    },
    [applyAuth],
  );

  const logout = useCallback(() => {
    clearAuth();
    setToken(null);
    setUser(null);
  }, []);

  const refreshMe = useCallback(async () => {
    if (!getStoredToken()) return;
    const me = await api.me();
    setUser(me);
    localStorage.setItem("untrade_user", JSON.stringify(me));
  }, []);

  const hasRole = useCallback(
    (role: UserRole) => !!user?.roles?.includes(role),
    [user],
  );

  const value = useMemo(
    () => ({
      user,
      token,
      loading,
      login,
      register,
      logout,
      refreshMe,
      hasRole,
    }),
    [user, token, loading, login, register, logout, refreshMe, hasRole],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
