"use client";

import React, { useState } from "react";
import { LayoutDashboard, LogOut, ShieldCheck, User as UserIcon } from "lucide-react";
import { useAuth } from "@/lib/auth";

interface AccountMenuProps {
  onNavigate: (tab: "dashboard" | "admin") => void;
}

/** "Sign in" for visitors; an avatar with a small menu (dashboard, admin reports, sign out) once signed in. */
export default function AccountMenu({ onNavigate }: AccountMenuProps) {
  const { ready, user, openSignIn, signOut } = useAuth();
  const [open, setOpen] = useState(false);

  if (!ready) return <div className="h-9 w-9" aria-hidden="true" />;
  if (!user) {
    return (
      <button
        onClick={openSignIn}
        aria-label="Sign in"
        className="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white p-2 text-xs font-bold sm:px-3 sm:py-1.5 text-slate-700 transition-colors hover:bg-slate-100 dark:border-glass dark:bg-slate-800 dark:text-gray-200 dark:hover:bg-slate-700"
      >
        <UserIcon className="h-4 w-4" />
        <span className="hidden sm:inline">Sign in</span>
      </button>
    );
  }

  const go = (tab: "dashboard" | "admin") => {
    setOpen(false);
    onNavigate(tab);
  };
  const item = "flex w-full items-center gap-2 rounded-lg px-2.5 py-2 text-left text-xs text-slate-700 hover:bg-slate-100 dark:text-gray-200 dark:hover:bg-slate-800";

  return (
    <div className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        aria-label="Account menu"
        aria-expanded={open}
        className="flex h-9 w-9 items-center justify-center overflow-hidden rounded-full border border-slate-200 bg-emerald-500 text-sm font-bold text-black dark:border-glass"
      >
        {user.picture ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={user.picture} alt="" referrerPolicy="no-referrer" className="h-full w-full object-cover" />
        ) : (
          (user.name || user.email)[0].toUpperCase()
        )}
      </button>
      {open && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
          <div className="absolute right-0 z-50 mt-2 w-64 rounded-panel border border-slate-200 bg-white p-1.5 shadow-lg dark:border-white/[0.12] dark:bg-surface-modal dark:shadow-modal dark:backdrop-blur-modal">
            <div className="border-b border-slate-200 px-2.5 pb-2 pt-1.5 dark:border-white/[0.08]">
              <p className="truncate text-xs font-bold text-slate-900 dark:text-white">{user.name || "Signed in"}</p>
              <p className="truncate text-[11px] text-slate-500 dark:text-gray-400">{user.email}</p>
              {user.role === "admin" && (
                <span className="mt-1 inline-block rounded-chip border border-amber-500/30 bg-amber-500/[0.12] px-1.5 font-mono text-[10px] font-semibold text-amber-600 dark:text-amber-400">
                  ADMIN
                </span>
              )}
            </div>
            <button className={item} onClick={() => go("dashboard")}>
              <LayoutDashboard className="h-4 w-4" /> My dashboard
            </button>
            {user.role === "admin" && (
              <button className={item} onClick={() => go("admin")}>
                <ShieldCheck className="h-4 w-4" /> Admin reports
              </button>
            )}
            <button
              className={item}
              onClick={() => {
                setOpen(false);
                signOut();
              }}
            >
              <LogOut className="h-4 w-4" /> Sign out
            </button>
          </div>
        </>
      )}
    </div>
  );
}
