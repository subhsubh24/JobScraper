'use client';

import { createContext, useContext, useEffect, useState } from 'react';
import { api, getToken } from '@/lib/api';
import type { User } from '@/lib/types';

interface AuthState {
  user: User | null;
  loading: boolean;
  setUser: (u: User | null) => void;
  signOut: () => void;
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthState | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        if (getToken()) setUser(await api.me());
      } catch {
        api.logout();
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  function signOut() {
    api.logout();
    setUser(null);
  }

  async function refresh() {
    setUser(await api.me());
  }

  return (
    <AuthContext.Provider value={{ user, loading, setUser, signOut, refresh }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
