"use client";

import React, { useState } from "react";
import { Database, Layers, Sun, Moon, Settings, Trophy, Wallet, ShieldCheck, BarChart3, LayoutDashboard } from "lucide-react";
import { useAuth } from "@/lib/auth";
import AccountMenu from "@/components/auth/AccountMenu";

interface HeaderProps {
  bankroll: number;
  onBankrollChange: (val: number) => void;
  dataSaver: boolean;
  onToggleDataSaver: () => void;
  activeTab: string;
  onSelectTab: (tab: string) => void;
  onOpenBankerModal: () => void;
  onOpenAccaBuilder?: (targetLegs: number) => void;
  showKelly: boolean;
  isDarkMode: boolean;
  onToggleTheme: () => void;
}

export default function Header({
  bankroll,
  onBankrollChange,
  dataSaver,
  onToggleDataSaver,
  activeTab,
  onSelectTab,
  onOpenAccaBuilder,
  showKelly,
  isDarkMode,
  onToggleTheme,
}: HeaderProps) {
  const [menuOpen, setMenuOpen] = useState(false);
  const { user } = useAuth();
  return (
    <header className="sticky top-0 z-40 hidden md:block bg-white/95 dark:bg-surface-glass backdrop-blur-md border-b border-slate-200 dark:border-gray-800 transition-colors duration-150">
      {/* Top Ticker: Live Lagos Market Insights */}
      <div className="bg-gradient-to-r from-emerald-600 via-emerald-700 to-teal-800 dark:from-emerald-950/90 dark:via-emerald-900/60 dark:to-black px-3.5 py-1 text-[11px] sm:text-xs flex justify-between items-center text-white dark:text-emerald-300 font-medium">
        <div className="flex items-center gap-1.5 truncate">
          <span className="flex h-2 w-2 rounded-full bg-emerald-300 animate-pulse shrink-0" />
          <span className="truncate">Predictions are probabilities, not guarantees. Every pick is locked before kickoff.</span>
        </div>
      </div>

      {/* Main Bar */}
      <div className="max-w-6xl mx-auto px-3.5 py-2.5 sm:py-3 flex justify-between items-center gap-2 sm:gap-4">
        {/* Brand */}
        <div className="flex items-center gap-2 cursor-pointer select-none" onClick={() => onSelectTab("fixtures")}>
          <div className="w-8 h-8 sm:w-9 sm:h-9 rounded-lg bg-emerald-600 dark:bg-gradient-to-br dark:from-emerald-500 dark:to-emerald-700 flex items-center justify-center font-black text-white dark:text-black text-base sm:text-lg shadow-sm">
            LB
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <h1 className="font-black text-base sm:text-lg tracking-tight text-slate-900 dark:text-white flex items-center gap-0.5">
                LIVELYBORG <span className="text-emerald-600 dark:text-emerald-400">AI</span>
              </h1>

            </div>
            <p className="text-[10px] text-slate-500 dark:text-gray-400 hidden xs:block -mt-0.5">Honest football predictions, trained on 70,000+ matches</p>
          </div>
        </div>

        {/* Center / Right Action Group */}
        <div className="flex items-center gap-1.5 sm:gap-2.5">
          <AccountMenu onNavigate={onSelectTab} />

          {/* Settings menu: theme + data saver */}
          <div className="relative">
            <button
              onClick={() => setMenuOpen((o) => !o)}
              className="p-1.5 sm:p-2 rounded-lg border border-slate-200 dark:border-glass bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-gray-300 transition-colors"
              aria-label="Settings"
              aria-expanded={menuOpen}
            >
              <Settings className="w-4 h-4" />
            </button>
            {menuOpen && (
              <>
                <div className="fixed inset-0 z-40" onClick={() => setMenuOpen(false)} />
                <div className="absolute right-0 mt-2 w-60 z-50 rounded-panel border border-slate-200 dark:border-white/[0.12] bg-white dark:bg-surface-modal dark:backdrop-blur-modal dark:shadow-modal p-1.5 text-xs">
                  <button
                    onClick={onToggleTheme}
                    className="w-full flex items-center justify-between gap-2 px-2.5 py-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-gray-200"
                  >
                    <span className="flex items-center gap-2">
                      {isDarkMode ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4" />}
                      {isDarkMode ? "Switch to light mode" : "Switch to dark mode"}
                    </span>
                  </button>
                  <button
                    onClick={onToggleDataSaver}
                    className="w-full flex items-center justify-between gap-2 px-2.5 py-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-gray-200 text-left"
                    title="Saves data for MTN / Airtel / Glo networks"
                  >
                    <span className="flex items-center gap-2">
                      <Database className="w-4 h-4" />
                      Data Saver
                    </span>
                    <span className={`font-mono text-[10px] font-semibold px-1.5 py-0.5 rounded-chip border ${dataSaver ? "text-amber-500 border-amber-500/30 bg-amber-500/[0.12]" : "text-slate-500 border-slate-300 dark:border-white/[0.08]"}`}>
                      {dataSaver ? "ON" : "OFF"}
                    </span>
                  </button>
                </div>
              </>
            )}
          </div>

          {/* Quick Bankroll Selector */}
          <div className="bg-slate-100 dark:bg-gray-900 border border-slate-200 dark:border-gray-700 rounded-lg px-2 py-1 flex items-center gap-1 text-xs">
            <span className="text-slate-500 dark:text-gray-400 font-medium hidden sm:inline">Capital:</span>
            <select
              value={bankroll}
              onChange={(e) => onBankrollChange(Number(e.target.value))}
              className="bg-transparent font-bold text-emerald-700 dark:text-emerald-400 focus:outline-none cursor-pointer"
            >
              <option value={5000} className="bg-white text-slate-900 dark:bg-gray-900 dark:text-white">₦5,000</option>
              <option value={10000} className="bg-white text-slate-900 dark:bg-gray-900 dark:text-white">₦10,000</option>
              <option value={20000} className="bg-white text-slate-900 dark:bg-gray-900 dark:text-white">₦20,000</option>
              <option value={50000} className="bg-white text-slate-900 dark:bg-gray-900 dark:text-white">₦50,000</option>
              <option value={100000} className="bg-white text-slate-900 dark:bg-gray-900 dark:text-white">₦100,000</option>
            </select>
          </div>
        </div>
      </div>

      {/* Navigation Sub-Tabs */}
      <div className="bg-slate-100/70 dark:bg-[#0B0F19] border-t border-slate-200 dark:border-gray-800/80 px-3.5">
        <div className="max-w-6xl mx-auto flex items-center gap-1 overflow-x-auto py-1 text-xs no-scrollbar">
          <button
            onClick={() => onSelectTab("fixtures")}
            className={`px-3 py-1.5 rounded-md font-bold whitespace-nowrap transition-colors flex items-center gap-1.5 ${
              activeTab === "fixtures"
                ? "bg-emerald-600 text-white dark:bg-emerald-500/20 dark:text-emerald-400 dark:border dark:border-emerald-500/40 shadow-xs"
                : "text-slate-600 hover:text-slate-900 dark:text-gray-400 dark:hover:text-white"
            }`}
          >
            <Trophy className="w-3.5 h-3.5" />
            <span>Matches & AI Picks</span>
          </button>

          {onOpenAccaBuilder && (
            <button
              onClick={() => onOpenAccaBuilder(5)}
              className="px-3 py-1.5 rounded-md font-bold whitespace-nowrap text-emerald-700 dark:text-emerald-400 hover:bg-emerald-100 dark:hover:bg-emerald-950/40 flex items-center gap-1"
            >
              <Layers className="w-3.5 h-3.5" />
              <span>Slip Builder</span>
            </button>
          )}

          {showKelly && (
            <button
              onClick={() => onSelectTab("bankroll")}
              className={`px-3 py-1.5 rounded-md font-bold whitespace-nowrap transition-colors flex items-center gap-1.5 ${
                activeTab === "bankroll"
                  ? "bg-emerald-600 text-white dark:bg-emerald-500/20 dark:text-emerald-400 dark:border dark:border-emerald-500/40 shadow-xs"
                  : "text-slate-600 hover:text-slate-900 dark:text-gray-400 dark:hover:text-white"
              }`}
            >
              <Wallet className="w-3.5 h-3.5" />
              <span>Stake Calculator</span>
            </button>
          )}

          <button
            onClick={() => onSelectTab("tracker")}
            className={`px-3 py-1.5 rounded-md font-bold whitespace-nowrap transition-colors flex items-center gap-1.5 ${
              activeTab === "tracker"
                ? "bg-emerald-600 text-white dark:bg-emerald-500/20 dark:text-emerald-400 dark:border dark:border-emerald-500/40 shadow-xs"
                : "text-slate-600 hover:text-slate-900 dark:text-gray-400 dark:hover:text-white"
            }`}
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Verified Track Record</span>
          </button>

          <button
            onClick={() => onSelectTab("accuracy")}
            className={`px-3 py-1.5 rounded-md font-bold whitespace-nowrap transition-colors flex items-center gap-1.5 ${
              activeTab === "accuracy"
                ? "bg-emerald-600 text-white dark:bg-emerald-500/20 dark:text-emerald-400 dark:border dark:border-emerald-500/40 shadow-xs"
                : "text-slate-600 hover:text-slate-900 dark:text-gray-400 dark:hover:text-white"
            }`}
          >
            <BarChart3 className="w-3.5 h-3.5" />
            <span>Accuracy</span>
          </button>
          {user && (
            <button
              onClick={() => onSelectTab("dashboard")}
              className={`px-3 py-1.5 rounded-md font-bold whitespace-nowrap transition-colors flex items-center gap-1.5 ${
                activeTab === "dashboard"
                  ? "bg-emerald-600 text-white dark:bg-emerald-500/20 dark:text-emerald-400 dark:border dark:border-emerald-500/40 shadow-xs"
                  : "text-slate-600 hover:text-slate-900 dark:text-gray-400 dark:hover:text-white"
              }`}
            >
              <LayoutDashboard className="w-3.5 h-3.5" />
              <span>My Dashboard</span>
            </button>
          )}

          {user?.role === "admin" && (
            <button
              onClick={() => onSelectTab("admin")}
              className={`px-3 py-1.5 rounded-md font-bold whitespace-nowrap transition-colors flex items-center gap-1.5 ${
                activeTab === "admin"
                  ? "bg-emerald-600 text-white dark:bg-emerald-500/20 dark:text-emerald-400 dark:border dark:border-emerald-500/40 shadow-xs"
                  : "text-slate-600 hover:text-slate-900 dark:text-gray-400 dark:hover:text-white"
              }`}
            >
              <ShieldCheck className="w-3.5 h-3.5 text-amber-500" />
              <span>Admin</span>
            </button>
          )}
        </div>
      </div>
    </header>
  );
}
