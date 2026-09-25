"use client";

import React from "react";
import { Zap, ShieldCheck, Send, Database, Sliders, Layers } from "lucide-react";

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
}: HeaderProps) {
  return (
    <header className="sticky top-0 z-40 bg-[#0d1322]/95 backdrop-blur-md border-b border-gray-800">
      {/* Top Ticker: Live Lagos Market Insights */}
      <div className="bg-gradient-to-r from-emerald-950/80 via-emerald-900/60 to-black px-4 py-1.5 text-xs flex justify-between items-center text-emerald-300 font-medium">
        <div className="flex items-center gap-2">
          <span className="flex h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
          <span>Lagos Value Alert: SportyBet line discrepancy on Arsenal (+14.2% EV)</span>
        </div>
        <div className="hidden sm:flex items-center gap-3">
          <span>Supported: <b>SportyBet</b> • <b>Bet9ja</b> • <b>BetKing</b></span>
          <span className="text-gray-500">|</span>
          <button 
            onClick={onOpenAdminModal}
            className="text-gold-400 hover:text-gold-300 underline font-semibold flex items-center gap-1"
          >
            Admin Panel
          </button>
        </div>
      </div>

      {/* Main Bar */}
      <div className="max-w-6xl mx-auto px-4 py-3 flex flex-wrap justify-between items-center gap-3">
        {/* Brand */}
        <div className="flex items-center gap-2 cursor-pointer" onClick={() => onSelectTab("fixtures")}>
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-emerald-500 to-emerald-700 flex items-center justify-center font-black text-black text-lg shadow-md">
            LB
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="font-extrabold text-lg tracking-tight text-white flex items-center gap-1">
                LIVELYBORG <span className="text-emerald-400">AI</span>
              </h1>
              <span className="text-[10px] uppercase font-bold px-1.5 py-0.5 rounded bg-gold-500/20 text-gold-400 border border-gold-500/30">
                Lagos Pro
              </span>
            </div>
            <p className="text-[11px] text-gray-400">Next-Gen Football Prediction & Bankroll Copilot</p>
          </div>
        </div>

        {/* Center / Right Action Group */}
        <div className="flex items-center gap-2 sm:gap-3">
          {/* Data Saver Mode Toggle */}
          <button
            onClick={onToggleDataSaver}
            className={`px-2.5 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all border ${
              dataSaver
                ? "bg-amber-950/70 border-amber-500/60 text-amber-300"
                : "bg-gray-800/80 border-gray-700 text-gray-300 hover:bg-gray-700"
            }`}
            title="Saves mobile data for MTN/Airtel/Glo users"
          >
            <Database className="w-3.5 h-3.5" />
            <span className="hidden xs:inline">{dataSaver ? "Data Saver: ON" : "Data Saver"}</span>
          </button>

          {/* Quick Bankroll Chip */}
          <div className="bg-gray-900 border border-gray-700 rounded-lg px-2.5 py-1 flex items-center gap-2 text-xs">
            <span className="text-gray-400 font-medium">Bankroll:</span>
            <select
              value={bankroll}
              onChange={(e) => onBankrollChange(Number(e.target.value))}
              className="bg-transparent font-bold text-emerald-400 focus:outline-none cursor-pointer"
            >
              <option value={5000} className="bg-gray-900 text-white">₦5,000</option>
              <option value={10000} className="bg-gray-900 text-white">₦10,000</option>
              <option value={20000} className="bg-gray-900 text-white">₦20,000</option>
              <option value={50000} className="bg-gray-900 text-white">₦50,000</option>
              <option value={100000} className="bg-gray-900 text-white">₦100,000</option>
            </select>
          </div>

          {/* Telegram VIP Channel */}
          <a
            href="https://t.me/"
            target="_blank"
            rel="noopener noreferrer"
            className="hidden md:flex items-center gap-1.5 bg-[#229ED9] hover:bg-[#1e8ec3] text-white text-xs font-bold px-3 py-1.5 rounded-lg transition-colors shadow-sm"
          >
            <Send className="w-3.5 h-3.5" />
            <span>Join VIP Telegram</span>
          </a>

          {/* 10-30 Games Acca Recommender Button */}
          {onOpenAccaBuilder && (
            <button
              onClick={() => onOpenAccaBuilder(10)}
              className="bg-emerald-600 hover:bg-emerald-500 text-black font-extrabold text-xs px-3 py-1.5 rounded-lg flex items-center gap-1.5 shadow-md transition-colors"
            >
              <Layers className="w-3.5 h-3.5 fill-black" />
              <span>10–30 Games Acca</span>
            </button>
          )}

          {/* Instant 2-Odds Banker Button */}
          <button
            onClick={onOpenBankerModal}
            className="bg-gradient-to-r from-gold-500 to-amber-600 hover:from-gold-400 hover:to-amber-500 text-black font-extrabold text-xs px-3 py-1.5 rounded-lg flex items-center gap-1.5 shadow-md glow-gold"
          >
            <Zap className="w-3.5 h-3.5 fill-black" />
            <span>Daily 2-Odds</span>
          </button>
        </div>
      </div>

      {/* Navigation Sub-Tabs */}
      <div className="bg-[#0b101c] border-t border-gray-800/80 px-4">
        <div className="max-w-6xl mx-auto flex items-center gap-1 overflow-x-auto py-1.5 text-xs no-scrollbar">
          <button
            onClick={() => onSelectTab("fixtures")}
            className={`px-3 py-1.5 rounded-md font-semibold whitespace-nowrap transition-colors ${
              activeTab === "fixtures"
                ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40"
                : "text-gray-400 hover:text-white"
            }`}
          >
            ⚽ Matches & AI Picks
          </button>

          {onOpenAccaBuilder && (
            <button
              onClick={() => onOpenAccaBuilder(10)}
              className="px-3 py-1.5 rounded-md font-semibold whitespace-nowrap text-emerald-400 hover:text-emerald-300 hover:bg-emerald-950/40 flex items-center gap-1.5 border border-emerald-500/30"
            >
              <Layers className="w-3.5 h-3.5" />
              <span>🎯 10–30 Game Acca Builder</span>
            </button>
          )}

          <button
            onClick={() => onSelectTab("bankroll")}
            className={`px-3 py-1.5 rounded-md font-semibold whitespace-nowrap transition-colors ${
              activeTab === "bankroll"
                ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40"
                : "text-gray-400 hover:text-white"
            }`}
          >
            💼 Kelly Bankroll Manager
          </button>

          <button
            onClick={() => onSelectTab("challenge")}
            className={`px-3 py-1.5 rounded-md font-semibold whitespace-nowrap transition-colors ${
              activeTab === "challenge"
                ? "bg-gold-500/20 text-gold-400 border border-gold-500/40"
                : "text-gray-400 hover:text-white"
            }`}
          >
            🚀 ₦1k → ₦50k Challenge
          </button>

          <button
            onClick={() => onSelectTab("tracker")}
            className={`px-3 py-1.5 rounded-md font-semibold whitespace-nowrap transition-colors ${
              activeTab === "tracker"
                ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40"
                : "text-gray-400 hover:text-white"
            }`}
          >
            🛡️ Verified Track Record
          </button>

          <button
            onClick={onOpenAdminModal}
            className="sm:hidden px-3 py-1.5 rounded-md font-semibold whitespace-nowrap text-gold-400 hover:text-gold-300"
          >
            ⚙️ Admin Panel
          </button>
        </div>
      </div>
    </header>
  );
}
