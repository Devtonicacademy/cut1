"use client";

import React, { useEffect, useState } from "react";
import { ShieldAlert } from "lucide-react";

const STORAGE_KEY = "livelyborg_age_confirmed";

function readConfirmed(): boolean {
  try {
    return localStorage.getItem(STORAGE_KEY) === "1";
  } catch {
    return false;
  }
}

/** Asks visitors to confirm they are 18+ before showing any predictions. */
export default function AgeGate({ children }: { children: React.ReactNode }) {
  const [status, setStatus] = useState<"checking" | "ask" | "ok" | "under18">("checking");

  useEffect(() => {
    setStatus(readConfirmed() ? "ok" : "ask");
  }, []);

  const confirm = () => {
    try {
      localStorage.setItem(STORAGE_KEY, "1");
    } catch {
      // storage blocked: confirmation lasts for this visit only
    }
    setStatus("ok");
  };

  if (status === "ok") return <>{children}</>;
  if (status === "checking") return null;

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-slate-50 dark:bg-[#090d16]">
      <div className="max-w-sm w-full bg-white dark:bg-[#0d1322] border border-slate-200 dark:border-gray-800 rounded-2xl p-6 shadow-sm text-center space-y-4">
        <ShieldAlert className="w-10 h-10 mx-auto text-amber-500" />
        {status === "ask" ? (
          <>
            <h1 className="text-lg font-black text-slate-900 dark:text-white">Are you 18 or older?</h1>
            <p className="text-xs text-slate-600 dark:text-gray-400 leading-relaxed">
              LivelyBorg AI publishes football predictions that relate to betting. It is only for adults.
              Predictions are probabilities, not guarantees.
            </p>
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => setStatus("under18")}
                className="py-2 rounded-xl text-sm font-bold bg-slate-100 dark:bg-gray-800 text-slate-700 dark:text-gray-300 border border-slate-200 dark:border-gray-700"
              >
                No
              </button>
              <button
                onClick={confirm}
                className="py-2 rounded-xl text-sm font-bold bg-emerald-600 hover:bg-emerald-700 text-white"
              >
                Yes, I&apos;m 18+
              </button>
            </div>
          </>
        ) : (
          <>
            <h1 className="text-lg font-black text-slate-900 dark:text-white">Sorry, this site is for adults only</h1>
            <p className="text-xs text-slate-600 dark:text-gray-400">You must be 18 or older to use LivelyBorg AI.</p>
          </>
        )}
      </div>
    </div>
  );
}
