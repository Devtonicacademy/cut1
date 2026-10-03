"use client";

import React, { useState } from "react";
import { AccumulatorResponse } from "@/types";
import { X, Copy, Check, ShieldAlert, Share2, Zap, Layers, RefreshCw, Info } from "lucide-react";

interface SmartAccaModalProps {
  data: AccumulatorResponse | null;
  bankroll: number;
  onClose: () => void;
  onOpenShareModal: () => void;
  onRebuildAcca?: (targetLegs: number, strategy: string) => Promise<void>;
  isLoading?: boolean;
}

const GAME_COUNTS = [2, 3, 5, 8, 10];
const STRATEGIES = [
  { key: "safest", label: "🛡️ Safer: double chance" },
  { key: "straight_win", label: "⚡ Straight wins" },
];

export default function SmartAccaModal({
  data,
  onClose,
  onOpenShareModal,
  onRebuildAcca,
  isLoading = false,
}: SmartAccaModalProps) {
  const [copied, setCopied] = useState(false);
  const [selectedGameCount, setSelectedGameCount] = useState<number>(data?.legs.length || 5);
  const [selectedStrategy, setSelectedStrategy] = useState<string>("safest");

  if (!data) return null;

  const rebuild = async (count: number, strategy: string) => {
    setSelectedGameCount(count);
    setSelectedStrategy(strategy);
    if (onRebuildAcca) await onRebuildAcca(count, strategy);
  };

  const copyMatchList = () => {
    try {
      navigator.clipboard.writeText(data.match_search_list || "");
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // clipboard unavailable
    }
  };

  const oneIn = data.win_probability > 0 ? Math.round(1 / data.win_probability) : null;
  const isEmpty = data.legs.length === 0;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/60 dark:bg-black/80 backdrop-blur-sm animate-in fade-in">
      <div className="bg-white dark:bg-[#111827] border border-slate-200 dark:border-gray-800 w-full max-w-2xl rounded-2xl overflow-hidden shadow-2xl flex flex-col max-h-[92vh]">
        {/* Header */}
        <div className="p-4 bg-gradient-to-r from-emerald-600 via-emerald-700 to-teal-800 dark:from-emerald-950 dark:via-gray-900 dark:to-black border-b border-emerald-500/20 dark:border-gray-800 flex justify-between items-center text-white">
          <div className="flex items-center gap-2.5">
            <span className="p-2 rounded-lg bg-amber-400 text-slate-900 dark:bg-gold-500/20 dark:text-gold-400">
              <Zap className="w-4 h-4 fill-current" />
            </span>
            <div>
              <h3 className="font-black text-sm sm:text-base flex items-center gap-2">
                <span>{isEmpty ? "Slip Builder" : data.ticket_type}</span>
                {isLoading && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
              </h3>
              <p className="text-[11px] opacity-80">Built from the model&apos;s most likely outcomes at real market prices</p>
            </div>
          </div>
          <button onClick={onClose} className="text-white/80 hover:text-white p-1 rounded-lg" aria-label="Close">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-4 overflow-y-auto space-y-4">
          {/* Controls */}
          <div className="bg-slate-50 dark:bg-[#1E293B] p-3 rounded-lg border border-slate-200 dark:border-gray-800 space-y-2">
            <span className="text-[11px] font-bold text-slate-700 dark:text-gray-300 uppercase tracking-wider flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
              <span>Number of games</span>
            </span>
            <div className="grid grid-cols-5 gap-1.5">
              {GAME_COUNTS.map((count) => (
                <button
                  key={count}
                  onClick={() => rebuild(count, selectedStrategy)}
                  disabled={isLoading}
                  className={`py-2 rounded-lg text-xs font-black border ${
                    selectedGameCount === count
                      ? "bg-emerald-600 text-white dark:bg-emerald-500 dark:text-black border-emerald-500"
                      : "bg-white dark:bg-gray-900 border-slate-200 dark:border-gray-800 text-slate-700 dark:text-gray-300"
                  }`}
                >
                  {count}
                </button>
              ))}
            </div>
            <div className="flex items-center gap-2 pt-1 border-t border-slate-200 dark:border-gray-800/60 overflow-x-auto text-xs no-scrollbar">
              <span className="text-[10px] text-slate-500 dark:text-gray-400 shrink-0">Picks:</span>
              {STRATEGIES.map((s) => (
                <button
                  key={s.key}
                  onClick={() => rebuild(selectedGameCount, s.key)}
                  disabled={isLoading}
                  className={`px-2.5 py-1 rounded text-[11px] font-bold whitespace-nowrap border ${
                    selectedStrategy === s.key
                      ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-500/20 dark:text-emerald-300 border-emerald-300 dark:border-emerald-500/40"
                      : "bg-white dark:bg-gray-900 text-slate-600 dark:text-gray-400 border-slate-200 dark:border-gray-800"
                  }`}
                >
                  {s.label}
                </button>
              ))}
            </div>
          </div>

          {isEmpty && (
            <div className="bg-slate-50 dark:bg-[#1E293B] border border-slate-200 dark:border-gray-800 rounded-lg p-5 text-center space-y-2">
              <Info className="w-6 h-6 mx-auto text-slate-400 dark:text-gray-500" />
              <h4 className="text-sm font-extrabold text-slate-900 dark:text-white">No slip available right now</h4>
              <p className="text-xs text-slate-600 dark:text-gray-400 leading-relaxed">
                Slips only use matches that have real market odds, and bookmaker prices usually appear 2-3 days before kickoff.
                Check back closer to the next matchday. Nothing has been priced yet, so we won&apos;t guess.
              </p>
            </div>
          )}

          {/* The honest numbers */}
          {!isEmpty && <>
          <div className="grid grid-cols-3 gap-2 bg-slate-50 dark:bg-[#1E293B] p-3 rounded-lg border border-slate-200 dark:border-gray-800 text-center">
            <div>
              <span className="text-[10px] text-slate-500 dark:text-gray-400 uppercase font-bold">Total odds</span>
              <p className="text-lg font-black text-slate-900 dark:text-white font-mono">{data.total_odds.toFixed(2)}</p>
            </div>
            <div>
              <span className="text-[10px] text-slate-500 dark:text-gray-400 uppercase font-bold">Chance all win</span>
              <p className="text-lg font-black text-emerald-600 dark:text-emerald-400 font-mono">
                {(data.win_probability * 100).toFixed(1)}%
              </p>
              {oneIn && <span className="text-[10px] text-slate-500 dark:text-gray-400">about 1 in {oneIn}</span>}
            </div>
            <div>
              <span className="text-[10px] text-slate-500 dark:text-gray-400 uppercase font-bold">Max stake (1%)</span>
              <p className="text-lg font-black text-amber-600 dark:text-gold-400 font-mono">₦{data.recommended_stake_ngn.toLocaleString()}</p>
              <span className="text-[10px] text-slate-500 dark:text-gray-400">pays ₦{data.potential_payout_ngn.toLocaleString()}</span>
            </div>
          </div>

          {data.cut_1_warning && (
            <div className="bg-amber-50 dark:bg-amber-950/40 border border-amber-300 dark:border-amber-500/40 rounded-lg p-3 flex items-start gap-2.5 text-xs text-amber-900 dark:text-amber-200">
              <ShieldAlert className="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
              <span className="leading-relaxed">{data.cut_1_warning}</span>
            </div>
          )}

          {data.recommended_game_count_note && (
            <div className="flex items-start gap-2 text-[11px] text-slate-600 dark:text-gray-400">
              <Info className="w-3.5 h-3.5 shrink-0 mt-0.5" />
              <span>{data.recommended_game_count_note}</span>
            </div>
          )}

          {/* Legs */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-bold text-slate-500 dark:text-gray-400 uppercase tracking-wider">Picks ({data.legs.length})</h4>
              <button
                onClick={copyMatchList}
                className="text-[11px] font-bold flex items-center gap-1 text-emerald-700 dark:text-emerald-400 hover:underline"
                title="Paste into SportyBet or Bet9ja search to find each match"
              >
                {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copied ? "Copied" : "Copy match list"}</span>
              </button>
            </div>
            {data.legs.map((leg, index) => (
              <div key={index} className="bg-slate-50 dark:bg-gray-900/60 border border-slate-200 dark:border-gray-800 p-2.5 rounded-lg flex justify-between items-center text-xs">
                <div className="min-w-0">
                  <span className="font-extrabold text-slate-900 dark:text-white block truncate">{leg.match_name}</span>
                  <span className="text-emerald-700 dark:text-emerald-400 font-semibold">{leg.market}</span>
                  {leg.league && <span className="text-[10px] text-slate-500 dark:text-gray-400 ml-1.5">• {leg.league}</span>}
                </div>
                <div className="text-right shrink-0 ml-2">
                  <span className="font-mono font-extrabold text-slate-900 dark:text-white text-sm">{leg.odds.toFixed(2)}</span>
                  <span className="block text-[10px] text-slate-500 dark:text-gray-400">{(leg.model_probability * 100).toFixed(0)}% likely</span>
                </div>
              </div>
            ))}
          </div>

          <p className="text-[10px] text-slate-500 dark:text-gray-400">
            Booking codes aren&apos;t available: add each match on your bookmaker&apos;s site. Predictions are probabilities, not guarantees. 18+.
          </p>
          </>}
        </div>

        <div className="p-3.5 bg-slate-50 dark:bg-gray-950 border-t border-slate-200 dark:border-gray-800 flex justify-between items-center gap-2">
          <button
            onClick={onOpenShareModal}
            disabled={data.legs.length === 0}
            className="bg-white dark:bg-gray-800 border border-slate-300 dark:border-gray-700 text-slate-800 dark:text-white font-bold text-xs px-4 py-2 rounded-lg flex items-center gap-1.5"
          >
            <Share2 className="w-3.5 h-3.5" />
            <span>Share</span>
          </button>
          <button onClick={onClose} className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs px-5 py-2 rounded-lg">
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
