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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/80 backdrop-blur-sm animate-in fade-in">
      <div className="bg-[#0e1424] border border-gray-800 w-full max-w-2xl rounded-2xl overflow-hidden shadow-2xl flex flex-col max-h-[92vh]">
        {/* Modal Header */}
        <div className="p-4 bg-gradient-to-r from-emerald-950 via-gray-900 to-black border-b border-gray-800 flex justify-between items-center">
          <div className="flex items-center gap-2.5">
            <span className="p-2 rounded-xl bg-gold-500/20 text-gold-400 border border-gold-500/30">
              <Zap className="w-4 h-4 fill-gold-400" />
            </span>
            <div>
              <h3 className="font-black text-sm sm:text-base text-white flex items-center gap-2">
                <span>{data.ticket_type}</span>
                {isLoading && <RefreshCw className="w-3.5 h-3.5 text-emerald-400 animate-spin" />}
              </h3>
              <p className="text-[11px] text-gray-400">
                Multi-League Statistical Predictor • Cut-1/Cut-2 Insured
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white p-1 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Content Scrollable */}
        <div className="p-4 overflow-y-auto space-y-4">
          {/* Quick Preset Selector for 5 to 30 Games */}
          <div className="bg-[#121a2c] p-3 rounded-xl border border-gray-800 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold text-gray-300 uppercase tracking-wider flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5 text-emerald-400" />
                <span>Select Number of Games at One Go:</span>
              </span>
              <span className="text-[10px] text-gold-400 font-bold bg-gold-500/10 px-2 py-0.5 rounded border border-gold-500/20">
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
                { count: 30, label: "30 Games", desc: "Giant Roll", rec: false },
              ].map((item) => (
                <button
                  key={item.count}
                  onClick={() => handleSelectCount(item.count)}
                  disabled={isLoading}
                  className={`p-2 rounded-lg text-center transition-all border flex flex-col items-center justify-center ${
                    selectedGameCount === item.count
                      ? "bg-emerald-500 text-black border-emerald-400 font-black shadow-md glow-emerald"
                      : "bg-gray-900 border-gray-800 text-gray-300 hover:border-gray-700 hover:text-white"
                  }`}
                >
                  <span className="text-xs font-black">{item.label}</span>
                  <span className={`text-[9px] font-semibold ${selectedGameCount === item.count ? "text-black" : "text-gray-400"}`}>
                    {item.desc}
                  </span>
                </button>
              ))}
            </div>

            {/* Strategy Filter Tabs */}
            <div className="flex items-center gap-2 pt-1 border-t border-gray-800/60 overflow-x-auto text-xs no-scrollbar">
              <span className="text-[10px] text-gray-400 shrink-0">Strategy:</span>
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
                      ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                      : "bg-gray-900 text-gray-400 hover:text-white border border-gray-800"
                  }`}
                >
                  {s.label}
                </button>
              ))}
            </div>
          </div>

          {/* AI Recommendation on Game Count */}
          <div className="bg-gradient-to-r from-emerald-950/40 via-gray-900/90 to-[#10192e] p-3.5 rounded-xl border border-emerald-500/30 text-xs space-y-1.5">
            <div className="flex items-center gap-1.5 text-gold-400 font-extrabold text-[11px] uppercase tracking-wide">
              <Sparkles className="w-3.5 h-3.5" />
              <span>LivelyBorg AI Game Count Recommendation:</span>
            </div>
            <p className="text-gray-300 text-[11px] leading-relaxed">
              <b>Recommended Sweet Spot: 5 to 10 Games</b> provides the highest mathematical survival probability (~15–25%) while still boosting your payout to <b>~10x to 35x</b>.
            </p>
            <p className="text-gray-400 text-[10px] leading-relaxed">
              When staking <b>15 to 30 games</b> at once, LivelyBorg automatically spreads your picks across <b>{data.leagues_covered?.length || 'multiple'} different leagues</b> and anchors on high-probability Double Chance (1X/X2). Always enable <b>SportyBet Flexi (Cut-1 / Cut-2)</b> and keep your stake small (₦100–₦250)!
            </p>
          </div>

          {/* Metrics Header Grid */}
          <div className="grid grid-cols-4 gap-2 bg-[#12192b] p-3 rounded-xl border border-gray-800 text-center">
            <div>
              <span className="text-[10px] text-gray-400 uppercase font-bold">Games</span>
              <p className="text-base sm:text-lg font-black text-white font-mono">
                {data.legs.length}
              </p>
            </div>
            <div>
              <span className="text-[10px] text-gray-400 uppercase font-bold">Total Odds</span>
              <p className="text-base sm:text-lg font-black text-emerald-400 font-mono">
                {data.total_odds.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </p>
            </div>
            <div>
              <span className="text-[10px] text-gray-400 uppercase font-bold">Rec. Stake</span>
              <p className="text-base sm:text-lg font-black text-gold-400 font-mono">
                ₦{data.recommended_stake_ngn.toLocaleString()}
              </p>
            </div>
            <div>
              <span className="text-[10px] text-gray-400 uppercase font-bold">Est. Payout</span>
              <p className="text-base sm:text-lg font-black text-emerald-300 font-mono">
                ₦{data.potential_payout_ngn.toLocaleString()}
              </p>
            </div>
          </div>

          {/* Cut Insurance Warning */}
          {data.cut_1_warning && (
            <div className="bg-amber-950/40 border border-amber-500/40 rounded-xl p-3 flex items-start gap-2.5 text-xs text-amber-200">
              <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
              <div>
                <span className="font-bold block text-amber-300">Cut-1 / Cut-2 Insurance Inspection:</span>
                <span className="text-[11px] leading-relaxed">{data.cut_1_warning}</span>
              </div>
            </div>
          )}

          {/* Leagues Covered Summary */}
          {data.leagues_covered && data.leagues_covered.length > 0 && (
            <div className="flex items-center gap-1.5 flex-wrap text-[10px]">
              <span className="text-gray-400 font-bold uppercase">Leagues ({data.leagues_covered.length}):</span>
              {data.leagues_covered.map((lg, i) => (
                <span key={i} className="bg-gray-800 text-gray-300 px-2 py-0.5 rounded font-semibold border border-gray-700">
                  {lg.replace("English ", "").replace("Spanish ", "").replace("Italian ", "").replace("German ", "").replace("French ", "")}
                </span>
              ))}
            </div>
          )}

          {/* Legs List */}
          <div className="space-y-2">
            <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider flex items-center justify-between">
              <span>Selected Picks ({data.legs.length} Matches):</span>
              <span className="text-[11px] text-emerald-400 font-normal">Sorted by Statistical Win Probability</span>
            </h4>
            <div className="space-y-1.5 max-h-72 overflow-y-auto pr-1">
              {data.legs.map((leg, i) => (
                <div
                  key={i}
                  className="bg-gray-900/70 p-2.5 rounded-xl border border-gray-800 flex justify-between items-center text-xs hover:border-gray-700 transition-colors"
                >
                  <div className="flex-1 min-w-0 pr-2">
                    <div className="flex items-center gap-1.5 flex-wrap">
                      <span className="text-emerald-400 font-bold text-[11px]">{i + 1}.</span>
                      {leg.league && (
                        <span className="text-[9px] uppercase font-bold px-1.5 py-0.2 rounded bg-gray-800 text-gray-400 border border-gray-700">
                          {leg.league.split(" ")[0]}
                        </span>
                      )}
                      <span className="font-bold text-white text-xs truncate">{leg.match_name}</span>
                    </div>
                    <div className="text-[11px] text-gray-300 mt-1 flex items-center gap-2 flex-wrap">
                      <span>Pick: <b className="text-emerald-300">{leg.market}</b></span>
                      <span className="text-gray-500">•</span>
                      <span>AI Win: <b className="text-white">{(leg.model_probability * 100).toFixed(0)}%</b></span>
                      {leg.likely_winner && (
                        <span className="text-[10px] text-amber-300 bg-amber-950/40 px-1 rounded">
                          Fav: {leg.likely_winner}
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="text-right shrink-0">
                    <span className="font-mono font-bold text-white text-xs sm:text-sm bg-gray-800 px-2 py-0.5 rounded">
                      {leg.odds.toFixed(2)}
                    </span>
                    <span className="block text-[9px] text-gold-400 font-semibold mt-0.5">
                      +{leg.ev_pct.toFixed(0)}% EV
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Booking Codes Box */}
          <div className="bg-[#121a2d] p-3.5 rounded-xl border border-emerald-500/30 space-y-2.5">
            <h4 className="text-xs font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-1.5">
              <span>Instant Booking Codes (1-Click Copy)</span>
            </h4>

            {/* SportyBet Code */}
            <div className="flex items-center justify-between bg-black/60 p-2.5 rounded-lg border border-gray-800">
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-red-400">SportyBet:</span>
                <span className="font-mono font-black text-sm text-white tracking-widest">
                  {data.sportybet_code}
                </span>
              </div>
              <button
                onClick={() => copyToClipboard(data.sportybet_code, true)}
                className="bg-red-700/80 hover:bg-red-600 text-white text-xs font-bold px-3 py-1.5 rounded-md flex items-center gap-1 transition-colors"
              >
                {copiedSporty ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copiedSporty ? "Copied!" : "Copy Code"}</span>
              </button>
            </div>

            {/* Bet9ja Code */}
            <div className="flex items-center justify-between bg-black/60 p-2.5 rounded-lg border border-gray-800">
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-green-500">Bet9ja:</span>
                <span className="font-mono font-black text-sm text-white tracking-widest">
                  {data.bet9ja_code}
                </span>
              </div>
              <button
                onClick={() => copyToClipboard(data.bet9ja_code, false)}
                className="bg-green-700/80 hover:bg-green-600 text-white text-xs font-bold px-3 py-1.5 rounded-md flex items-center gap-1 transition-colors"
              >
                {copiedBet9ja ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copiedBet9ja ? "Copied!" : "Copy Code"}</span>
              </button>
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="p-4 bg-gray-900 border-t border-gray-800 flex flex-wrap justify-between items-center gap-2">
          <button
            onClick={onOpenShareModal}
            className="flex items-center gap-1.5 bg-emerald-600 hover:bg-emerald-500 text-black text-xs font-black px-4 py-2 rounded-xl transition-colors shadow-md"
          >
            <Share2 className="w-3.5 h-3.5" />
            <span>Share {data.legs.length}-Game Ticket to WhatsApp</span>
          </button>

          <button
            onClick={onClose}
            className="text-xs font-semibold text-gray-400 hover:text-white px-3 py-2"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
