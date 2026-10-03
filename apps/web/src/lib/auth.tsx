"use client";

import React, { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { API_BASE_URL } from "@/lib/config";
import { AppUser, SavedFixture } from "@/types";

/** fetch against the API with the session cookie attached. Returns the parsed JSON, or null on any failure. */
export async function apiJson<T>(path: string, init?: RequestInit): Promise<{ ok: boolean; status: number; data: T | null }> {
  try {
    const res = await fetch(`${API_BASE_URL}${path}`, {
      credentials: "include",
      ...init,
      headers: { ...(init?.body ? { "Content-Type": "application/json" } : {}), ...init?.headers },
    });
    return { ok: res.ok, status: res.status, data: res.ok ? ((await res.json()) as T) : null };
  } catch {
    return { ok: false, status: 0, data: null };
  }
}

interface AuthState {
  ready: boolean;
  user: AppUser | null;
  /** Public Google client id from the server; null when sign-in is not configured. */
  googleClientId: string | null;
  saved: SavedFixture[];
  savedIds: Set<string>;
  signInOpen: boolean;
  signInError: string | null;
  /** True right after a fresh sign-in (not when a session is restored), so the page can open the admin view once. */
  justSignedIn: boolean;
  openSignIn: () => void;
  closeSignIn: () => void;
  acknowledgeSignIn: () => void;
  handleCredential: (credential: string) => Promise<void>;
  signOut: () => Promise<void>;
  /** Saves or un-saves a fixture. Signed-out visitors are asked to sign in first and it is saved afterwards. */
  toggleSave: (fixtureId: string) => Promise<void>;
}

const AuthContext = createContext<AuthState | null>(null);

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [ready, setReady] = useState(false);
  const [user, setUser] = useState<AppUser | null>(null);
  const [googleClientId, setGoogleClientId] = useState<string | null>(null);
  const [saved, setSaved] = useState<SavedFixture[]>([]);
  const [signInOpen, setSignInOpen] = useState(false);
  const [signInError, setSignInError] = useState<string | null>(null);
  const [justSignedIn, setJustSignedIn] = useState(false);
  const pendingSave = useRef<string | null>(null);

  const loadSaved = useCallback(async () => {
    const res = await apiJson<SavedFixture[]>("/me/saved");
    setSaved(res.data ?? []);
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const [config, me] = await Promise.all([
        apiJson<{ google_client_id: string | null }>("/auth/config"),
        apiJson<{ user: AppUser | null }>("/auth/me"),
      ]);
      if (cancelled) return;
      setGoogleClientId(config.data?.google_client_id ?? null);
      setUser(me.data?.user ?? null);
      if (me.data?.user) await loadSaved();
      if (!cancelled) setReady(true);
    })();
    return () => {
      cancelled = true;
    };
  }, [loadSaved]);

  const save = useCallback(async (fixtureId: string) => {
    const res = await apiJson<SavedFixture[]>("/me/saved", { method: "POST", body: JSON.stringify({ fixture_id: fixtureId }) });
    if (res.data) setSaved(res.data);
  }, []);

  const handleCredential = useCallback(async (credential: string) => {
    setSignInError(null);
    const res = await apiJson<{ user: AppUser | null }>("/auth/google", { method: "POST", body: JSON.stringify({ credential }) });
    if (!res.data?.user) {
      setSignInError(res.status === 401 ? "Google could not verify that sign-in. Please try again." : "Could not reach the server. Please try again.");
      return;
    }
    setUser(res.data.user);
    setJustSignedIn(true);
    setSignInOpen(false);
    await loadSaved();
    if (pendingSave.current) {
      const id = pendingSave.current;
      pendingSave.current = null;
      await save(id);
    }
  }, [loadSaved, save]);

  const signOut = useCallback(async () => {
    await apiJson("/auth/logout", { method: "POST" });
    setUser(null);
    setSaved([]);
    setJustSignedIn(false);
  }, []);

  const savedIds = useMemo(() => new Set(saved.map((s) => s.fixture_id)), [saved]);

  const toggleSave = useCallback(async (fixtureId: string) => {
    if (!user) {
      pendingSave.current = fixtureId;
      setSignInError(null);
      setSignInOpen(true);
      return;
    }
    if (savedIds.has(fixtureId)) {
      setSaved((prev) => prev.filter((s) => s.fixture_id !== fixtureId)); // optimistic
      const res = await apiJson<SavedFixture[]>(`/me/saved/${encodeURIComponent(fixtureId)}`, { method: "DELETE" });
      if (res.data) setSaved(res.data);
      else await loadSaved();
    } else {
      await save(fixtureId);
    }
  }, [user, savedIds, loadSaved, save]);

  const value: AuthState = {
    ready, user, googleClientId, saved, savedIds, signInOpen, signInError, justSignedIn,
    openSignIn: () => { pendingSave.current = null; setSignInError(null); setSignInOpen(true); },
    closeSignIn: () => { pendingSave.current = null; setSignInOpen(false); },
    acknowledgeSignIn: () => setJustSignedIn(false),
    handleCredential, signOut, toggleSave,
  };
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
