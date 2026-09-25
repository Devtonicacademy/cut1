"use client";

import React, { useState } from "react";
import { AccumulatorResponse } from "@/types";
import { X, Copy, Check, ShieldAlert, Share2, Zap, Trophy, Shield, Sparkles, Layers, RefreshCw } from "lucide-react";

interface SmartAccaModalProps {
  data: AccumulatorResponse | null;
  bankroll: number;
  onClose: () => void;
  onOpenShareModal: () => void;
  onRebuildAcca?: (targetLegs: number, strategy: string) => Promise<void>;
  isLoading?: boolean;
}

export default function SmartAccaModal({
  data,
  bankroll,
  onClose,
  onOpenShareModal,
  onRebuildAcca,
  isLoading = false
}: SmartAccaModalProps) {
  const [copiedSporty, setCopiedSporty] = useState(false);
  const [copiedBet9ja, setCopiedBet9ja] = useState(false);
  const [selectedGameCount, setSelectedGameCount] = useState<number>(data?.legs.length || 10);
  const [selectedStrategy, setSelectedStrategy] = useState<string>("safest_winners");

  if (!data) return null;

  const copyToClipboard = (text: string, isSporty: boolean) => {
    navigator.clipboard.writeText(text);
    if (isSporty) {
      setCopiedSporty(true);
      setTimeout(() => setCopiedSporty(false), 2000);
    } else {
      setCopiedBet9ja(true);
      setTimeout(() => setCopiedBet9ja(false), 2000);
    }
  };

  const handleSelectCount = async (count: number) => {
    setSelectedGameCount(count);
    if (onRebuildAcca) {
      await onRebuildAcca(count, selectedStrategy);
    }
  };

  const handleSelectStrategy = async (strat: string) => {
    setSelectedStrategy(strat);
    if (onRebuildAcca) {
      await onRebuildAcca(selectedGameCount, strat);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/60 dark:bg-black/80 backdrop-blur-sm animate-in fade-in">
      <div className="bg-white dark:bg-[#0e1424] border border-slate-200 dark:border-gray-800 w-full max-w-2xl rounded-2xl overflow-hidden shadow-2xl flex flex-col max-h-[92vh]">
        {/* Modal Header */}
        <div className="p-4 bg-gradient-to-r from-emerald-600 via-emerald-700 to-teal-800 dark:from-emerald-950 dark:via-gray-900 dark:to-black border-b border-emerald-500/20 dark:border-gray-800 flex justify-between items-center text-white">
          <div className="flex items-center gap-2.5">
            <span className="p-2 rounded-xl bg-amber-400 text-slate-900 dark:bg-gold-500/20 dark:text-gold-400 border border-amber-300 dark:border-gold-500/30">
              <Zap className="w-4 h-4 fill-current" />
            </span>
            <div>
              <h3 className="font-black text-sm sm:text-base flex items-center gap-2">
                <span>{data.ticket_type}</span>
                {isLoading && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
              </h3>
              <p className="text-[11px] opacity-80">
                Multi-League Statistical Predictor • Cut-1/Cut-2 Insured
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-white/80 hover:text-white p-1 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Content Scrollable */}
        <div className="p-4 overflow-y-auto space-y-4">
          {/* Quick Preset Selector for 5 to 30 Games */}
          <div className="bg-slate-50 dark:bg-[#121a2c] p-3 rounded-xl border border-slate-200 dark:border-gray-800 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold text-slate-700 dark:text-gray-300 uppercase tracking-wider flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
                <span>Select Number of Games:</span>
              </span>
              <span className="text-[10px] text-amber-800 dark:text-gold-400 font-bold bg-amber-100 dark:bg-gold-500/10 px-2 py-0.5 rounded border border-amber-300 dark:border-gold-500/20">
                {data.legs.length} Games Active
              </span>
            </div>

            <div className="grid grid-cols-3 sm:grid-cols-6 gap-1.5">
              {[
                { count: 5, label: "5 Games", desc: "Sweet Spot", rec: true },
                { count: 10, label: "10 Games", desc: "Balanced", rec: true },
                { count: 15, label: "15 Games", desc: "Super Acca", rec: false },
                { count: 20, label: "20 Games", desc: "Mega Slip", rec: false },
                { count: 25, label: "25 Games", desc: "Cut-2 Ins.", rec: false },
                { count: 30, label: "30 Games", desc: "Jackpot Roll", rec: false },
              ].map((item) => (
                <button
                  key={item.count}
                  onClick={() => handleSelectCount(item.count)}
                  disabled={isLoading}
                  className={`p-2 rounded-lg text-center transition-all border flex flex-col items-center justify-center ${
                    selectedGameCount === item.count
                      ? "bg-emerald-600 text-white dark:bg-emerald-500 dark:text-black border-emerald-500 font-black shadow-sm"
                      : "bg-white dark:bg-gray-900 border-slate-200 dark:border-gray-800 text-slate-700 dark:text-gray-300 hover:border-slate-300 dark:hover:border-gray-700"
                  }`}
                >
                  <span className="text-xs font-black">{item.label}</span>
                  <span className={`text-[9px] font-semibold ${selectedGameCount === item.count ? "opacity-90" : "text-slate-400 dark:text-gray-500"}`}>
                    {item.desc}
                  </span>
                </button>
              ))}
            </div>

            {/* Strategy Filter Tabs */}
            <div className="flex items-center gap-2 pt-1 border-t border-slate-200 dark:border-gray-800/60 overflow-x-auto text-xs no-scrollbar">
              <span className="text-[10px] text-slate-500 dark:text-gray-400 shrink-0">Strategy:</span>
              {[
                { key: "safest_winners", label: "🛡️ Safest Statistical Anchors" },
                { key: "straight_win", label: "⚡ Straight Winners Only" },
                { key: "balanced_value", label: "📈 +EV Value Mix" },
              ].map((s) => (
                <button
                  key={s.key}
                  onClick={() => handleSelectStrategy(s.key)}
                  disabled={isLoading}
                  className={`px-2.5 py-1 rounded text-[11px] font-bold whitespace-nowrap transition-colors ${
                    selectedStrategy === s.key
                      ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-500/20 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-500/40"
                      : "bg-white dark:bg-gray-900 text-slate-600 dark:text-gray-400 hover:text-slate-900 dark:hover:text-white border border-slate-200 dark:border-gray-800"
                  }`}
                >
                  {s.label}
                </button>
              ))}
            </div>
          </div>

          {/* Metrics Header Grid */}
          <div className="grid grid-cols-4 gap-2 bg-slate-50 dark:bg-[#12192b] p-3 rounded-xl border border-slate-200 dark:border-gray-800 text-center">
            <div>
              <span className="text-[10px] text-slate-500 dark:text-gray-400 uppercase font-bold">Games</span>
              <p className="text-base sm:text-lg font-black text-slate-900 dark:text-white font-mono">
                {data.legs.length}
              </p>
            </div>
            <div>
              <span className="text-[10px] text-slate-500 dark:text-gray-400 uppercase font-bold">Total Odds</span>
              <p className="text-base sm:text-lg font-black text-emerald-600 dark:text-emerald-400 font-mono">
                {data.total_odds.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </p>
            </div>
            <div>
              <span className="text-[10px] text-slate-500 dark:text-gray-400 uppercase font-bold">Rec. Stake</span>
              <p className="text-base sm:text-lg font-black text-amber-600 dark:text-gold-400 font-mono">
                ₦{data.recommended_stake_ngn.toLocaleString()}
              </p>
            </div>
            <div>
              <span className="text-[10px] text-slate-500 dark:text-gray-400 uppercase font-bold">Est. Payout</span>
              <p className="text-base sm:text-lg font-black text-emerald-700 dark:text-emerald-300 font-mono">
                ₦{data.potential_payout_ngn.toLocaleString()}
              </p>
            </div>
          </div>

          {/* Cut Insurance Warning */}
          {data.cut_1_warning && (
            <div className="bg-amber-50 dark:bg-amber-950/40 border border-amber-300 dark:border-amber-500/40 rounded-xl p-3 flex items-start gap-2.5 text-xs text-amber-900 dark:text-amber-200">
              <ShieldAlert className="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
              <div>
                <span className="font-bold block text-amber-800 dark:text-amber-300">Cut-1 / Cut-2 Insurance Inspection:</span>
                <span className="text-[11px] leading-relaxed">{data.cut_1_warning}</span>
              </div>
            </div>
          )}

          {/* Booking Codes Box */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {/* SportyBet */}
            <div className="bg-rose-50 dark:bg-red-950/20 border border-rose-200 dark:border-red-900/60 p-3 rounded-xl flex justify-between items-center">
              <div>
                <span className="text-[10px] text-rose-700 dark:text-red-400 font-bold uppercase">SportyBet Booking Code</span>
                <div className="text-lg font-mono font-black text-slate-900 dark:text-white mt-0.5">
                  {data.sportybet_code}
                </div>
              </div>
              <button
                onClick={() => copyToClipboard(data.sportybet_code, true)}
                className="bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition-colors shadow-sm"
              >
                {copiedSporty ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copiedSporty ? "Copied" : "Copy"}</span>
              </button>
            </div>

            {/* Bet9ja */}
            <div className="bg-emerald-50 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-900/60 p-3 rounded-xl flex justify-between items-center">
              <div>
                <span className="text-[10px] text-emerald-700 dark:text-emerald-400 font-bold uppercase">Bet9ja Booking Code</span>
                <div className="text-lg font-mono font-black text-slate-900 dark:text-white mt-0.5">
                  {data.bet9ja_code}
                </div>
              </div>
              <button
                onClick={() => copyToClipboard(data.bet9ja_code, false)}
                className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition-colors shadow-sm"
              >
                {copiedBet9ja ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copiedBet9ja ? "Copied" : "Copy"}</span>
              </button>
            </div>
          </div>

          {/* List of Match Legs */}
          <div className="space-y-2">
            <h4 className="text-xs font-bold text-slate-500 dark:text-gray-400 uppercase tracking-wider">
              Selected Match Legs ({data.legs.length}):
            </h4>
            <div className="space-y-1.5">
              {data.legs.map((leg, index) => (
                <div
                  key={index}
                  className="bg-slate-50 dark:bg-gray-900/60 border border-slate-200 dark:border-gray-800 p-2.5 rounded-xl flex justify-between items-center text-xs"
                >
                  <div className="truncate max-w-[220px] sm:max-w-none">
                    <span className="font-extrabold text-slate-900 dark:text-white block truncate">{leg.match_name}</span>
                    <span className="text-emerald-700 dark:text-emerald-400 font-semibold">{leg.market}</span>
                    {leg.league && <span className="text-[10px] text-slate-400 dark:text-gray-500 ml-1.5">• {leg.league}</span>}
                  </div>
                  <div className="text-right shrink-0">
                    <span className="font-mono font-extrabold text-slate-900 dark:text-white text-sm">{leg.odds.toFixed(2)}</span>
                    <span className="block text-[10px] text-slate-400 dark:text-gray-500">{(leg.model_probability * 100).toFixed(0)}% Prob</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="p-3.5 bg-slate-50 dark:bg-gray-950 border-t border-slate-200 dark:border-gray-800 flex justify-between items-center gap-2">
          <button
            onClick={onOpenShareModal}
            className="bg-white dark:bg-gray-800 border border-slate-300 dark:border-gray-700 text-slate-800 dark:text-white font-bold text-xs px-4 py-2 rounded-xl flex items-center gap-1.5 hover:bg-slate-100 dark:hover:bg-gray-700 transition-colors"
          >
            <Share2 className="w-3.5 h-3.5" />
            <span>Share Ticket</span>
          </button>

          <button
            onClick={onClose}
            className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs px-5 py-2 rounded-xl transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
