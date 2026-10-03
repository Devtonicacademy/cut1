"use client";

import React, { useEffect, useRef } from "react";
import { createPortal } from "react-dom";
import { Bookmark, X } from "lucide-react";
import { useAuth } from "@/lib/auth";
import GoogleButton from "@/components/auth/GoogleButton";

/** Opens when a visitor asks to sign in, or tries to save a fixture while signed out. */
export default function SignInModal() {
  const { signInOpen, closeSignIn, googleClientId, handleCredential, signInError, ready } = useAuth();
  const closeRef = useRef<HTMLButtonElement>(null);
  const closeFn = useRef(closeSignIn);
  closeFn.current = closeSignIn;

  useEffect(() => {
    if (!signInOpen) return;
    const previous = document.activeElement as HTMLElement | null;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && closeFn.current();
    document.addEventListener("keydown", onKey);
    const overflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    closeRef.current?.focus();
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = overflow;
      previous?.focus();
    };
  }, [signInOpen]);

  if (!signInOpen || typeof document === "undefined") return null;

  return createPortal(
    <div className="fixed inset-0 z-[80] flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/50 backdrop-blur-md" onClick={closeSignIn} aria-hidden="true" />
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Sign in"
        className="relative w-full max-w-sm rounded-panel border border-slate-200 bg-white p-6 text-center shadow-modal dark:border-white/[0.12] dark:bg-surface-modal dark:backdrop-blur-modal"
      >
        <button
          ref={closeRef}
          onClick={closeSignIn}
          aria-label="Close"
          className="absolute right-3 top-3 rounded-lg p-1.5 text-slate-500 hover:bg-slate-100 dark:text-gray-400 dark:hover:bg-slate-800"
        >
          <X className="h-5 w-5" />
        </button>
        <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-emerald-500/[0.12] text-emerald-500">
          <Bookmark className="h-6 w-6" />
        </div>
        <h2 className="font-display text-lg font-semibold text-slate-900 dark:text-white">Sign in to save fixtures</h2>
        <p className="mb-5 mt-1 text-xs leading-relaxed text-slate-600 dark:text-gray-400">
          Keep the matches you care about on your own dashboard, with the model&apos;s prediction and the final result.
        </p>
        {!ready ? (
          <p className="text-xs text-slate-500 dark:text-gray-400">Loading…</p>
        ) : googleClientId ? (
          <GoogleButton clientId={googleClientId} onCredential={handleCredential} />
        ) : (
          <p className="rounded-lg border border-amber-500/30 bg-amber-500/[0.12] p-3 text-xs text-amber-600 dark:text-amber-400">
            Sign-in is not set up on this server yet.
          </p>
        )}
        {signInError && <p role="alert" className="mt-3 text-xs text-rose-500">{signInError}</p>}
        <p className="mt-5 text-[11px] text-slate-500 dark:text-gray-400">We only use your Google name, email and photo to identify your account.</p>
      </div>
    </div>,
    document.body,
  );
}
