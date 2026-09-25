"use client";

import React from "react";
import { Zap, ShieldCheck, Send, Database, Sliders, Layers, Sun, Moon, Shield, Award } from "lucide-react";

interface HeaderProps {
  bankroll: number;
  onBankrollChange: (val: number) => void;
  dataSaver: boolean;
  onToggleDataSaver: () => void;
  activeTab: string;
  onSelectTab: (tab: string) => void;
  onOpenBankerModal: () => void;
  onOpenAdminModal: () => void;
  onOpenAccaBuilder?: (targetLegs: number) => void;
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
  onOpenBankerModal,
  onOpenAdminModal,
  onOpenAccaBuilder,
  isDarkMode,
  onToggleTheme,
}: HeaderProps) {
  return (
    <header className="sticky top-0 z-40 bg-white/95 dark:bg-[#0d1322]/95 backdrop-blur-md border-b border-slate-200 dark:border-gray-800 transition-colors duration-150">
      {/* Top Ticker: Live Lagos Market Insights */}
      <div className="bg-gradient-to-r from-emerald-600 via-emerald-700 to-teal-800 dark:from-emerald-950/90 dark:via-emerald-900/60 dark:to-black px-3.5 py-1 text-[11px] sm:text-xs flex justify-between items-center text-white dark:text-emerald-300 font-medium">
        <div className="flex items-center gap-1.5 truncate">
          <span className="flex h-2 w-2 rounded-full bg-emerald-300 animate-pulse shrink-0" />
          <span className="truncate">Lagos Value Alert: SportyBet line discrepancy on Arsenal (+14.2% EV)</span>
        </div>
        <div className="hidden md:flex items-center gap-3 shrink-0">
          <span>Supported: <b>SportyBet</b> • <b>Bet9ja</b> • <b>BetKing</b></span>
          <span className="opacity-40">|</span>
          <button 
            onClick={onOpenAdminModal}
            className="text-amber-200 dark:text-gold-400 hover:underline font-bold flex items-center gap-1"
          >
            Admin Panel
          </button>
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
              <span className="text-[9px] uppercase font-bold px-1 py-0.2 rounded bg-amber-100 text-amber-800 dark:bg-gold-500/20 dark:text-gold-400 border border-amber-300 dark:border-gold-500/30">
                PRO
              </span>
            </div>
            <p className="text-[10px] text-slate-500 dark:text-gray-400 hidden xs:block -mt-0.5">Lagos Football Intelligence & Bankroll Copilot</p>
          </div>
        </div>

        {/* Center / Right Action Group */}
        <div className="flex items-center gap-1.5 sm:gap-2.5">
          {/* Light / Dark Mode Toggle */}
          <button
            onClick={onToggleTheme}
            className="p-1.5 sm:p-2 rounded-lg border border-slate-200 dark:border-gray-700 bg-slate-100 hover:bg-slate-200 dark:bg-gray-800 dark:hover:bg-gray-700 text-slate-700 dark:text-gray-300 transition-colors shadow-2xs"
            title={isDarkMode ? "Switch to Clean Light Mode" : "Switch to Dark Mode"}
            aria-label="Toggle theme"
          >
            {isDarkMode ? (
              <Sun className="w-4 h-4 text-amber-400 animate-in spin-in-90 duration-200" />
            ) : (
              <Moon className="w-4 h-4 text-slate-700 animate-in spin-in-90 duration-200" />
            )}
          </button>

          {/* Data Saver Mode Toggle */}
          <button
            onClick={onToggleDataSaver}
            className={`px-2 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1 transition-all border ${
              dataSaver
                ? "bg-amber-100 dark:bg-amber-950/70 border-amber-400 text-amber-900 dark:text-amber-300"
                : "bg-slate-100 dark:bg-gray-800/80 border-slate-200 dark:border-gray-700 text-slate-600 dark:text-gray-300 hover:bg-slate-200 dark:hover:bg-gray-700"
            }`}
            title="Saves data for MTN / Airtel / Glo networks"
          >
            <Database className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">{dataSaver ? "Data Saver: ON" : "Data Saver"}</span>
          </button>

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

          {/* Acca Builder Quick Button */}
          {onOpenAccaBuilder && (
            <button
              onClick={() => onOpenAccaBuilder(10)}
              className="hidden lg:flex items-center gap-1 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs px-2.5 py-1.5 rounded-lg shadow-sm transition-colors"
            >
              <Layers className="w-3.5 h-3.5" />
              <span>Acca Builder</span>
            </button>
          )}

          {/* Instant 2-Odds Banker Button */}
          <button
            onClick={onOpenBankerModal}
            className="bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-600 hover:to-amber-700 text-white dark:text-black font-extrabold text-xs px-2.5 sm:px-3 py-1.5 rounded-lg flex items-center gap-1 shadow-sm transition-all"
          >
            <Zap className="w-3.5 h-3.5 fill-current" />
            <span className="whitespace-nowrap">2-Odds Banker</span>
          </button>
        </div>
      </div>

      {/* Navigation Sub-Tabs */}
      <div className="bg-slate-100/70 dark:bg-[#0b101c] border-t border-slate-200 dark:border-gray-800/80 px-3.5">
        <div className="max-w-6xl mx-auto flex items-center gap-1 overflow-x-auto py-1 text-xs no-scrollbar">
          <button
            onClick={() => onSelectTab("fixtures")}
            className={`px-3 py-1.5 rounded-md font-bold whitespace-nowrap transition-colors ${
              activeTab === "fixtures"
                ? "bg-emerald-600 text-white dark:bg-emerald-500/20 dark:text-emerald-400 dark:border dark:border-emerald-500/40 shadow-xs"
                : "text-slate-600 hover:text-slate-900 dark:text-gray-400 dark:hover:text-white"
            }`}
          >
            ⚽ Matches & AI Picks
          </button>

          {onOpenAccaBuilder && (
            <button
              onClick={() => onOpenAccaBuilder(10)}
              className="px-3 py-1.5 rounded-md font-bold whitespace-nowrap text-emerald-700 dark:text-emerald-400 hover:bg-emerald-100 dark:hover:bg-emerald-950/40 flex items-center gap-1"
            >
              <Layers className="w-3.5 h-3.5" />
              <span>🎯 10–30 Games Acca</span>
            </button>
          )}

          <button
            onClick={() => onSelectTab("bankroll")}
            className={`px-3 py-1.5 rounded-md font-bold whitespace-nowrap transition-colors ${
              activeTab === "bankroll"
                ? "bg-emerald-600 text-white dark:bg-emerald-500/20 dark:text-emerald-400 dark:border dark:border-emerald-500/40 shadow-xs"
                : "text-slate-600 hover:text-slate-900 dark:text-gray-400 dark:hover:text-white"
            }`}
          >
            💼 Kelly Calculator
          </button>

          <button
            onClick={() => onSelectTab("challenge")}
            className={`px-3 py-1.5 rounded-md font-bold whitespace-nowrap transition-colors ${
              activeTab === "challenge"
                ? "bg-amber-500 text-white dark:bg-gold-500/20 dark:text-gold-400 dark:border dark:border-gold-500/40 shadow-xs"
                : "text-slate-600 hover:text-slate-900 dark:text-gray-400 dark:hover:text-white"
            }`}
          >
            🚀 ₦1k → ₦50k Ladder
          </button>

          <button
            onClick={() => onSelectTab("tracker")}
            className={`px-3 py-1.5 rounded-md font-bold whitespace-nowrap transition-colors ${
              activeTab === "tracker"
                ? "bg-emerald-600 text-white dark:bg-emerald-500/20 dark:text-emerald-400 dark:border dark:border-emerald-500/40 shadow-xs"
                : "text-slate-600 hover:text-slate-900 dark:text-gray-400 dark:hover:text-white"
            }`}
          >
            🛡️ Verified Track Record
          </button>

          <button
            onClick={onOpenAdminModal}
            className="md:hidden px-3 py-1.5 rounded-md font-bold whitespace-nowrap text-amber-700 dark:text-gold-400 hover:underline ml-auto"
          >
            ⚙️ Admin
          </button>
        </div>
      </div>
    </header>
  );
}
