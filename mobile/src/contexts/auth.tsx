import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';

import { api, getToken } from '@/services/api';
import { identifyUser } from '@/services/purchases';
import type { User } from '@/types';

interface AuthState {
  user: User | null;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (input: {
    email: string;
    password: string;
    full_name?: string;
    resume_text?: string;
  }) => Promise<void>;
  signOut: () => Promise<void>;
  refresh: () => Promise<void>;
  // Directly set the cached user (e.g. after an endpoint returns the updated user, like the
  // AI-consent grant/revoke) — avoids a redundant /me round-trip.
  setUser: (u: User | null) => void;
}

const AuthContext = createContext<AuthState | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // Restore a saved session on launch.
  useEffect(() => {
    (async () => {
      try {
        const token = await getToken();
        if (token) {
          const u = await api.me();
          setUser(u);
          // Link the RevenueCat identity to this user (no-op when IAP is unconfigured).
          void identifyUser(u.id);
        }
      } catch {
        // Stale/invalid token — stay logged out, no crash.
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const signIn = useCallback(async (email: string, password: string) => {
    const u = await api.login(email, password);
    setUser(u);
    void identifyUser(u.id);
  }, []);

  const signUp = useCallback<AuthState['signUp']>(async (input) => {
    const u = await api.register(input);
    setUser(u);
    void identifyUser(u.id);
  }, []);

  const signOut = useCallback(async () => {
    await api.logout();
    setUser(null);
  }, []);

  const refresh = useCallback(async () => {
    setUser(await api.me());
  }, []);

  const value = useMemo<AuthState>(
    () => ({ user, loading, signIn, signUp, signOut, refresh, setUser }),
    [user, loading, signIn, signUp, signOut, refresh],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
