"use client";

import React, { useEffect, useRef, useState } from "react";

interface GoogleId {
  initialize: (config: { client_id: string; callback: (r: { credential: string }) => void; auto_select?: boolean }) => void;
  renderButton: (el: HTMLElement, options: Record<string, string | number>) => void;
}
declare global {
  interface Window {
    google?: { accounts: { id: GoogleId } };
  }
}

const SCRIPT_SRC = "https://accounts.google.com/gsi/client";

function loadGoogleScript(): Promise<void> {
  if (window.google?.accounts?.id) return Promise.resolve();
  return new Promise((resolve, reject) => {
    const existing = document.querySelector<HTMLScriptElement>(`script[src="${SCRIPT_SRC}"]`);
    const script = existing ?? Object.assign(document.createElement("script"), { src: SCRIPT_SRC, async: true, defer: true });
    script.addEventListener("load", () => resolve());
    script.addEventListener("error", () => reject(new Error("Could not load Google sign-in")));
    if (!existing) document.head.appendChild(script);
  });
}

/** Renders Google's own "Sign in with Google" button. The returned credential is verified on the server. */
export default function GoogleButton({ clientId, onCredential }: { clientId: string; onCredential: (credential: string) => void }) {
  const holder = useRef<HTMLDivElement>(null);
  const [failed, setFailed] = useState(false);
  const callback = useRef(onCredential);
  callback.current = onCredential;

  useEffect(() => {
    let cancelled = false;
    loadGoogleScript()
      .then(() => {
        if (cancelled || !holder.current || !window.google) return;
        window.google.accounts.id.initialize({ client_id: clientId, callback: (r) => callback.current(r.credential), auto_select: false });
        window.google.accounts.id.renderButton(holder.current, { theme: "filled_black", size: "large", shape: "pill", text: "signin_with", width: 280 });
      })
      .catch(() => !cancelled && setFailed(true));
    return () => {
      cancelled = true;
    };
  }, [clientId]);

  if (failed) {
    return <p className="text-xs text-amber-500">Google sign-in could not load. Check your connection or ad blocker and try again.</p>;
  }
  return <div ref={holder} className="flex min-h-[44px] justify-center" />;
}
