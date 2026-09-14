// Auth context with token refresh support
'use client';

import React, { createContext, useContext, useEffect, useState, useCallback, useRef } from 'react';
import { login as apiLogin, logout as apiLogout, refreshToken, AuthResponse } from '@/lib/api';

interface AuthContextType {
  user: { email: string } | null;
  token: string | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  getValidToken: () => Promise<string | null>;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  token: null,
  isLoading: true,
  login: async () => {},
  logout: async () => {},
  getValidToken: async () => null,
});

const STORAGE_KEY = 'ivy_auth';

interface StoredAuth {
  access_token: string;
  refresh_token: string;
  expires_at: number; // Unix timestamp in ms
  user: { email: string };
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<{ email: string } | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const refreshTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const storeAuth = (data: AuthResponse) => {
    const stored: StoredAuth = {
      access_token: data.access_token,
      refresh_token: data.refresh_token,
      expires_at: Date.now() + (data.expires_in * 1000) - 60000, // 60s buffer
      user: data.user,
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(stored));
    setToken(data.access_token);
    setUser(data.user);
    return stored;
  };

  const clearAuth = () => {
    localStorage.removeItem(STORAGE_KEY);
    setToken(null);
    setUser(null);
    if (refreshTimerRef.current) {
      clearTimeout(refreshTimerRef.current);
    }
  };

  const scheduleRefresh = useCallback((stored: StoredAuth) => {
    if (refreshTimerRef.current) {
      clearTimeout(refreshTimerRef.current);
    }
    const delay = stored.expires_at - Date.now() - 30000; // refresh 30s before expiry
    if (delay > 0) {
      refreshTimerRef.current = setTimeout(async () => {
        try {
          const newAuth = await refreshToken(stored.refresh_token);
          const newStored = storeAuth(newAuth);
          scheduleRefresh(newStored);
        } catch (e) {
          console.error('Token refresh failed:', e);
          clearAuth();
        }
      }, delay);
    }
  }, []);

  // Try to refresh token
  const doRefresh = useCallback(async (refreshTok: string): Promise<string | null> => {
    try {
      const newAuth = await refreshToken(refreshTok);
      const newStored = storeAuth(newAuth);
      scheduleRefresh(newStored);
      return newAuth.access_token;
    } catch {
      clearAuth();
      return null;
    }
  }, [scheduleRefresh]);

  // Load from storage on mount
  useEffect(() => {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      try {
        const stored: StoredAuth = JSON.parse(raw);
        if (Date.now() < stored.expires_at) {
          setToken(stored.access_token);
          setUser(stored.user);
          scheduleRefresh(stored);
        } else {
          // Token expired, try refresh
          doRefresh(stored.refresh_token);
        }
      } catch {
        clearAuth();
      }
    }
    setIsLoading(false);
  }, [scheduleRefresh, doRefresh]);

  const getValidToken = useCallback(async (): Promise<string | null> => {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    try {
      const stored: StoredAuth = JSON.parse(raw);
      if (Date.now() < stored.expires_at) {
        return stored.access_token;
      }
      return await doRefresh(stored.refresh_token);
    } catch {
      return null;
    }
  }, [doRefresh]);

  const login = useCallback(async (email: string, password: string) => {
    const data = await apiLogin(email, password);
    const stored = storeAuth(data);
    scheduleRefresh(stored);
  }, [scheduleRefresh]);

  const logout = useCallback(async () => {
    if (token) {
      try { await apiLogout(token); } catch { /* ignore */ }
    }
    clearAuth();
  }, [token]);

  return (
    <AuthContext.Provider value={{ user, token, isLoading, login, logout, getValidToken }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
