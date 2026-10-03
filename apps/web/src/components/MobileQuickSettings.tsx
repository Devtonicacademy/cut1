"use client";

import React from "react";
import { Database, Moon, Sun } from "lucide-react";
import AccountMenu from "@/components/auth/AccountMenu";

interface MobileQuickSettingsProps {
  bankroll: number;
  onBankrollChange: (val: number) => void;
  dataSaver: boolean;
  onToggleDataSaver: () => void;
  isDarkMode: boolean;
  onToggleTheme: () => void;
  onNavigate: (tab: "dashboard" | "admin") => void;
}

const BANKROLLS = [5000, 10000, 20000, 50000, 100000];

/** Phone-only settings strip. The header is hidden below `md`, so its controls live here, in the page. */
export default function MobileQuickSettings({
  bankroll,
  onBankrollChange,
  dataSaver,
  onToggleDataSaver,
  isDarkMode,
  onToggleTheme,
  onNavigate,
}: MobileQuickSettingsProps) {
  const iconBtn =
    "rounded-lg border border-slate-200 bg-white p-2 text-slate-700 dark:border-glass dark:bg-slate-800 dark:text-gray-200";
  return (
    <div className="mb-4 flex items-center justify-between gap-2 md:hidden">
      <div className="flex items-center gap-2">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-500 text-base font-black text-black">LB</div>
        <span className="font-display text-base font-black tracking-tight text-slate-900 dark:text-white">
          LIVELYBORG <span className="text-emerald-500">AI</span>
        </span>
      </div>
      <div className="flex items-center gap-1.5">
        <label className="flex items-center gap-1 rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-xs dark:border-glass dark:bg-slate-800">
          <span className="sr-only">Capital</span>
          <select
            value={bankroll}
            onChange={(e) => onBankrollChange(Number(e.target.value))}
            className="cursor-pointer bg-transparent font-mono font-bold text-emerald-600 focus:outline-none dark:text-emerald-400"
          >
            {BANKROLLS.map((b) => (
              <option key={b} value={b} className="bg-white text-slate-900 dark:bg-slate-900 dark:text-white">
                ₦{b.toLocaleString()}
              </option>
            ))}
          </select>
        </label>
        <button
          onClick={onToggleDataSaver}
          aria-pressed={dataSaver}
          aria-label="Data Saver"
          title="Saves data for MTN / Airtel / Glo networks"
          className={`${iconBtn} ${dataSaver ? "!border-amber-500/40 !bg-amber-500/[0.12] !text-amber-500" : ""}`}
        >
          <Database className="h-4 w-4" />
        </button>
        <AccountMenu onNavigate={onNavigate} />
        <button onClick={onToggleTheme} aria-label="Toggle theme" className={iconBtn}>
          {isDarkMode ? <Sun className="h-4 w-4 text-amber-400" /> : <Moon className="h-4 w-4" />}
        </button>
      </div>
    </div>
  );
}
