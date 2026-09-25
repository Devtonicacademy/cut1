"use client";

import React from "react";
import { Zap, Layers, Calculator, ShieldCheck, Trophy, Sparkles } from "lucide-react";

interface MobileBottomNavProps {
  activeTab: string;
  onSelectTab: (tab: string) => void;
  onOpenBankerModal: () => void;
  onOpenAccaBuilder?: (targetLegs: number) => void;
}

export default function MobileBottomNav({
  activeTab,
  onSelectTab,
  onOpenBankerModal,
  onOpenAccaBuilder,
}: MobileBottomNavProps) {
  return (
    <nav className="md:hidden fixed bottom-0 left-0 right-0 z-40 bg-white/95 dark:bg-[#0d1322]/95 backdrop-blur-lg border-t border-slate-200 dark:border-gray-800 px-2 py-1.5 shadow-lg safe-bottom">
      <div className="flex justify-around items-center max-w-md mx-auto">
        {/* Matches */}
        <button
          onClick={() => onSelectTab("fixtures")}
          className={`flex flex-col items-center justify-center py-1 px-2 rounded-lg transition-colors text-[10px] font-bold ${
            activeTab === "fixtures"
              ? "text-emerald-600 dark:text-emerald-400"
              : "text-slate-500 dark:text-gray-400 hover:text-slate-900 dark:hover:text-gray-200"
          }`}
        >
          <Trophy className="w-5 h-5 mb-0.5" />
          <span>Matches</span>
        </button>

        {/* 2-Odds Banker */}
        <button
          onClick={onOpenBankerModal}
          className="flex flex-col items-center justify-center py-1 px-2 rounded-lg text-[10px] font-extrabold text-amber-600 dark:text-amber-400"
        >
          <div className="w-7 h-7 rounded-full bg-amber-500 text-white dark:text-black flex items-center justify-center shadow-xs -mt-2 mb-0.5">
            <Zap className="w-4 h-4 fill-current" />
          </div>
          <span>2-Odds</span>
        </button>

        {/* 10-30 Games Acca */}
        {onOpenAccaBuilder && (
          <button
            onClick={() => onOpenAccaBuilder(10)}
            className="flex flex-col items-center justify-center py-1 px-2 rounded-lg transition-colors text-[10px] font-bold text-slate-500 dark:text-gray-400 hover:text-emerald-600 dark:hover:text-emerald-400"
          >
            <Layers className="w-5 h-5 mb-0.5" />
            <span>Accas</span>
          </button>
        )}

        {/* Kelly Bankroll Manager */}
        <button
          onClick={() => onSelectTab("bankroll")}
          className={`flex flex-col items-center justify-center py-1 px-2 rounded-lg transition-colors text-[10px] font-bold ${
            activeTab === "bankroll"
              ? "text-emerald-600 dark:text-emerald-400"
              : "text-slate-500 dark:text-gray-400 hover:text-slate-900 dark:hover:text-gray-200"
          }`}
        >
          <Calculator className="w-5 h-5 mb-0.5" />
          <span>Kelly</span>
        </button>

        {/* ₦1k -> ₦50k Ladder Challenge */}
        <button
          onClick={() => onSelectTab("challenge")}
          className={`flex flex-col items-center justify-center py-1 px-2 rounded-lg transition-colors text-[10px] font-bold ${
            activeTab === "challenge"
              ? "text-amber-600 dark:text-gold-400"
              : "text-slate-500 dark:text-gray-400 hover:text-slate-900 dark:hover:text-gray-200"
          }`}
        >
          <Sparkles className="w-5 h-5 mb-0.5" />
          <span>₦50k Ladder</span>
        </button>
      </div>
    </nav>
  );
}
