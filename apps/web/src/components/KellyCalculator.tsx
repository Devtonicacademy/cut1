"use client";

import React, { useState } from "react";
import { ValueBetItem, RiskLevel } from "@/types";
import { Shield, Zap, TrendingUp, DollarSign, ArrowRight, Trash2 } from "lucide-react";

interface KellyCalculatorProps {
  bankroll: number;
  onBankrollChange: (val: number) => void;
  selectedBets: ValueBetItem[];
  onRemoveBet: (betIndex: number) => void;
  onGenerateBookingSlip: () => void;
}

export default function KellyCalculator({
  bankroll,
  onBankrollChange,
  selectedBets,
  onRemoveBet,
  onGenerateBookingSlip,
}: KellyCalculatorProps) {
  const [riskLevel, setRiskLevel] = useState<RiskLevel>("conservative");

  // Multiplier mapping
  const riskMultipliers: Record<RiskLevel, { fraction: number; maxSinglePct: number; label: string; desc: string }> = {
    conservative: {
      fraction: 0.15,
      maxSinglePct: 0.025,
      label: "🛡️ Conservative",
      desc: "Stakes 1.0%–2.5% max. Capital preservation & drawdown shield."
    },
    balanced: {
      fraction: 0.25,
      maxSinglePct: 0.045,
      label: "⚖️ Balanced",
      desc: "Stakes 2.0%–4.5% on verified +EV plays. Optimal risk-adjusted growth."
    },
    aggressive: {
      fraction: 0.40,
      maxSinglePct: 0.070,
      label: "🚀 High Growth",
      desc: "Stakes 3.5%–7.0% on top plays. Higher variance for faster expansion."
    }
  };

  const currentRisk = riskMultipliers[riskLevel];

  // Calculate allocation
  const calculatedAllocations = selectedBets.map((b) => {
    const rawKelly = ((b.market_odds - 1) * b.model_probability - (1 - b.model_probability)) / (b.market_odds - 1);
    const stakeFraction = Math.min(currentRisk.maxSinglePct, Math.max(0.01, rawKelly * currentRisk.fraction));
    const rawStake = bankroll * stakeFraction;
    const roundedStake = Math.max(100, Math.round(rawStake / 50) * 50);
    const potentialPayout = Math.round(roundedStake * b.market_odds);
    const expectedProfit = Math.round(roundedStake * (b.expected_value_pct / 100));

    return {
      ...b,
      final_stake: roundedStake,
      potential_payout: potentialPayout,
      expected_profit: expectedProfit,
      stake_pct: ((roundedStake / bankroll) * 100).toFixed(1)
    };
  });

  const totalStaked = calculatedAllocations.reduce((acc, curr) => acc + curr.final_stake, 0);
  const totalExpectedProfit = calculatedAllocations.reduce((acc, curr) => acc + curr.expected_profit, 0);
  const remainingBankroll = Math.max(0, bankroll - totalStaked);

  return (
    <div className="bg-white dark:bg-[#0d1322] border border-slate-200 dark:border-gray-800 rounded-2xl p-4 sm:p-6 shadow-sm max-w-4xl mx-auto transition-colors duration-150">
      {/* Title & Intro */}
      <div className="flex flex-wrap justify-between items-center gap-3 border-b border-slate-200 dark:border-gray-800 pb-4 mb-5">
        <div>
          <h2 className="text-base sm:text-xl font-black text-slate-900 dark:text-white flex items-center gap-2">
            <DollarSign className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
            <span>Naira Bankroll & Kelly Staking Copilot</span>
          </h2>
          <p className="text-xs text-slate-500 dark:text-gray-400 mt-0.5">
            Fractional Kelly sizing eliminates accumulator wipes on SportyBet & Bet9ja.
          </p>
        </div>

        {/* Selected Counter */}
        <span className="bg-emerald-50 dark:bg-emerald-950/80 border border-emerald-300 dark:border-emerald-500/50 text-emerald-800 dark:text-emerald-300 text-xs font-bold px-3 py-1 rounded-full">
          {selectedBets.length} Plays Selected
        </span>
      </div>

      {/* Bankroll Slider Controls */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-5 bg-slate-50 dark:bg-gray-900/60 p-4 rounded-xl border border-slate-200 dark:border-gray-800">
        <div>
          <div className="flex justify-between items-center mb-1 text-xs">
            <span className="text-slate-700 dark:text-gray-300 font-semibold">Your Total Capital:</span>
            <span className="text-base sm:text-lg font-black text-emerald-600 dark:text-emerald-400 font-mono">
              ₦{bankroll.toLocaleString()}
            </span>
          </div>
          <input
            type="range"
            min={2000}
            max={200000}
            step={1000}
            value={bankroll}
            onChange={(e) => onBankrollChange(Number(e.target.value))}
            className="w-full h-2 bg-slate-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer accent-emerald-500"
          />
          <div className="flex justify-between text-[10px] text-slate-400 dark:text-gray-500 mt-1">
            <span>₦2,000</span>
            <span>₦50,000</span>
            <span>₦100,000</span>
            <span>₦200,000</span>
          </div>
        </div>

        {/* Risk Profile Selector */}
        <div>
          <label className="text-xs font-semibold text-slate-700 dark:text-gray-300 block mb-1.5">
            Risk Profile Strategy:
          </label>
          <div className="grid grid-cols-3 gap-1.5">
            {(["conservative", "balanced", "aggressive"] as RiskLevel[]).map((lvl) => (
              <button
                key={lvl}
                onClick={() => setRiskLevel(lvl)}
                className={`py-1.5 px-2 rounded-lg text-xs font-bold capitalize transition-all border ${
                  riskLevel === lvl
                    ? "bg-emerald-600 text-white dark:bg-emerald-500 dark:text-black border-emerald-500 shadow-sm"
                    : "bg-white dark:bg-gray-800 text-slate-700 dark:text-gray-300 border-slate-200 dark:border-gray-700 hover:bg-slate-100 dark:hover:bg-gray-700"
                }`}
              >
                {lvl}
              </button>
            ))}
          </div>
          <p className="text-[11px] text-slate-500 dark:text-gray-400 mt-1.5 italic">
            {currentRisk.desc}
          </p>
        </div>
      </div>

      {/* Staking Summary Cards */}
      <div className="grid grid-cols-3 gap-2.5 sm:gap-3 mb-5">
        <div className="bg-slate-50 dark:bg-[#11192e] p-3 rounded-xl border border-slate-200 dark:border-gray-800 text-center">
          <p className="text-[10px] uppercase font-bold text-slate-500 dark:text-gray-400">Total Staked</p>
          <p className="text-sm sm:text-lg font-black text-slate-900 dark:text-white font-mono mt-0.5">
            ₦{totalStaked.toLocaleString()}
          </p>
          <p className="text-[10px] text-slate-500 dark:text-gray-400">
            {((totalStaked / bankroll) * 100).toFixed(1)}% of capital
          </p>
        </div>

        <div className="bg-emerald-50 dark:bg-[#11192e] p-3 rounded-xl border border-emerald-200 dark:border-gray-800 text-center">
          <p className="text-[10px] uppercase font-bold text-emerald-800 dark:text-gray-400">Expected Profit</p>
          <p className="text-sm sm:text-lg font-black text-emerald-700 dark:text-emerald-400 font-mono mt-0.5">
            +₦{totalExpectedProfit.toLocaleString()}
          </p>
          <p className="text-[10px] text-emerald-600 dark:text-emerald-300/80">+EV edge</p>
        </div>

        <div className="bg-slate-50 dark:bg-[#11192e] p-3 rounded-xl border border-slate-200 dark:border-gray-800 text-center">
          <p className="text-[10px] uppercase font-bold text-slate-500 dark:text-gray-400">Reserve Capital</p>
          <p className="text-sm sm:text-lg font-black text-blue-700 dark:text-blue-300 font-mono mt-0.5">
            ₦{remainingBankroll.toLocaleString()}
          </p>
          <p className="text-[10px] text-slate-500 dark:text-gray-400">Safe in account</p>
        </div>
      </div>

      {/* Allocation List */}
      {selectedBets.length === 0 ? (
        <div className="text-center py-8 bg-slate-50 dark:bg-gray-900/30 rounded-xl border border-dashed border-slate-200 dark:border-gray-800">
          <p className="text-slate-600 dark:text-gray-400 text-sm font-medium">No value bets selected yet.</p>
          <p className="text-slate-400 dark:text-gray-500 text-xs mt-1">
            Tap &quot;Stake&quot; on any match card to calculate your optimal Naira stake.
          </p>
        </div>
      ) : (
        <div className="space-y-2 mb-5">
          <h3 className="text-xs font-bold text-slate-500 dark:text-gray-400 uppercase tracking-wider mb-2">
            Optimal Stake Allocation:
          </h3>
          {calculatedAllocations.map((item, idx) => (
            <div
              key={idx}
              className="bg-slate-50 dark:bg-gray-900/80 border border-slate-200 dark:border-gray-800 p-3 rounded-xl flex flex-wrap justify-between items-center gap-3 transition-colors"
            >
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-extrabold text-sm text-slate-900 dark:text-white">{item.market_name}</span>
                  <span className="bg-emerald-100 dark:bg-emerald-950 text-emerald-800 dark:text-emerald-400 text-[10px] font-bold px-1.5 py-0.5 rounded border border-emerald-300 dark:border-emerald-500/40">
                    +{item.expected_value_pct.toFixed(1)}% EV
                  </span>
                </div>
                <p className="text-xs text-slate-500 dark:text-gray-400 mt-0.5">
                  Best odds on <b className="text-slate-800 dark:text-white">{item.bookmaker}</b>: <b className="text-emerald-700 dark:text-emerald-400 font-mono">{item.market_odds.toFixed(2)}</b> (Fair Odds: {item.fair_odds.toFixed(2)})
                </p>
              </div>

              <div className="flex items-center gap-3">
                <div className="text-right">
                  <div className="text-sm font-black text-emerald-700 dark:text-emerald-400 font-mono">
                    ₦{item.final_stake.toLocaleString()}
                  </div>
                  <div className="text-[10px] text-slate-500 dark:text-gray-400">
                    Payout: ₦{item.potential_payout.toLocaleString()} ({item.stake_pct}%)
                  </div>
                </div>

                <button
                  onClick={() => onRemoveBet(idx)}
                  className="text-slate-400 hover:text-rose-500 dark:text-gray-500 dark:hover:text-red-400 p-1.5 transition-colors"
                  title="Remove from slip"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Action Footer */}
      {selectedBets.length > 0 && (
        <div className="flex flex-wrap justify-between items-center gap-3 pt-4 border-t border-slate-200 dark:border-gray-800">
          <p className="text-xs text-slate-500 dark:text-gray-400">
            Ready to load on SportyBet or Bet9ja?
          </p>

          <button
            onClick={onGenerateBookingSlip}
            className="w-full sm:w-auto bg-emerald-600 hover:bg-emerald-700 text-white font-extrabold px-6 py-2.5 rounded-xl shadow-md flex items-center justify-center gap-2 text-sm transition-all"
          >
            <span>Generate SportyBet & Bet9ja Codes</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  );
}
