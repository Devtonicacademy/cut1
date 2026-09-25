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
      label: "🛡️ Conservative (Capital Preservation)",
      desc: "Stakes 1.0%–2.5% max. Focus on steady bankroll compounding and avoiding drawdowns."
    },
    balanced: {
      fraction: 0.25,
      maxSinglePct: 0.045,
      label: "⚖️ Balanced (Value Hunter)",
      desc: "Stakes 2.0%–4.5% on verified +EV plays. Optimal risk-adjusted bankroll growth."
    },
    aggressive: {
      fraction: 0.40,
      maxSinglePct: 0.070,
      label: "🚀 High Growth (Aggressive)",
      desc: "Stakes 3.5%–7.0% on top plays. Higher short-term variance for faster bankroll expansion."
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
    <div className="bg-[#0d1322] border border-gray-800 rounded-2xl p-5 shadow-xl max-w-4xl mx-auto">
      {/* Title & Intro */}
      <div className="flex flex-wrap justify-between items-center gap-3 border-b border-gray-800 pb-4 mb-5">
        <div>
          <h2 className="text-lg sm:text-xl font-extrabold text-white flex items-center gap-2">
            <DollarSign className="w-5 h-5 text-emerald-400" />
            <span>Naira Bankroll & Fractional Kelly Staking Advisor</span>
          </h2>
          <p className="text-xs text-gray-400 mt-0.5">
            Never guess your stake again. Dynamic sizing eliminates bankroll wipes on SportyBet & Bet9ja.
          </p>
        </div>

        {/* Selected Counter */}
        <span className="bg-emerald-950/80 border border-emerald-500/50 text-emerald-300 text-xs font-bold px-3 py-1 rounded-full">
          {selectedBets.length} Value Plays Selected
        </span>
      </div>

      {/* Bankroll Slider Controls */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6 bg-gray-900/60 p-4 rounded-xl border border-gray-800">
        <div>
          <div className="flex justify-between items-center mb-1 text-xs">
            <span className="text-gray-300 font-semibold">Your Total Capital (Bankroll):</span>
            <span className="text-lg font-black text-emerald-400 font-mono">
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
            className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-emerald-500"
          />
          <div className="flex justify-between text-[10px] text-gray-500 mt-1">
            <span>₦2,000</span>
            <span>₦50,000</span>
            <span>₦100,000</span>
            <span>₦200,000</span>
          </div>
        </div>

        {/* Risk Profile Selector */}
        <div>
          <label className="text-xs font-semibold text-gray-300 block mb-1.5">
            Risk Tolerance Strategy:
          </label>
          <div className="grid grid-cols-3 gap-1.5">
            {(["conservative", "balanced", "aggressive"] as RiskLevel[]).map((lvl) => (
              <button
                key={lvl}
                onClick={() => setRiskLevel(lvl)}
                className={`py-1.5 px-2 rounded-lg text-xs font-bold capitalize transition-all border ${
                  riskLevel === lvl
                    ? "bg-emerald-500 text-black border-emerald-400 shadow-sm"
                    : "bg-gray-800 text-gray-300 border-gray-700 hover:bg-gray-700"
                }`}
              >
                {lvl}
              </button>
            ))}
          </div>
          <p className="text-[11px] text-gray-400 mt-1.5 italic">
            {currentRisk.desc}
          </p>
        </div>
      </div>

      {/* Staking Summary Cards */}
      <div className="grid grid-cols-3 gap-3 mb-6">
        <div className="bg-[#11192e] p-3 rounded-xl border border-gray-800 text-center">
          <p className="text-[10px] uppercase font-bold text-gray-400">Total Staked</p>
          <p className="text-sm sm:text-lg font-black text-white font-mono mt-0.5">
            ₦{totalStaked.toLocaleString()}
          </p>
          <p className="text-[10px] text-gray-400">
            {((totalStaked / bankroll) * 100).toFixed(1)}% of bankroll
          </p>
        </div>

        <div className="bg-[#11192e] p-3 rounded-xl border border-gray-800 text-center">
          <p className="text-[10px] uppercase font-bold text-gray-400">Expected Profit (+EV)</p>
          <p className="text-sm sm:text-lg font-black text-emerald-400 font-mono mt-0.5">
            +₦{totalExpectedProfit.toLocaleString()}
          </p>
          <p className="text-[10px] text-emerald-300/80">Mathematical edge</p>
        </div>

        <div className="bg-[#11192e] p-3 rounded-xl border border-gray-800 text-center">
          <p className="text-[10px] uppercase font-bold text-gray-400">Remaining Capital</p>
          <p className="text-sm sm:text-lg font-black text-blue-300 font-mono mt-0.5">
            ₦{remainingBankroll.toLocaleString()}
          </p>
          <p className="text-[10px] text-gray-400">Preserved in reserve</p>
        </div>
      </div>

      {/* Allocation List */}
      {selectedBets.length === 0 ? (
        <div className="text-center py-8 bg-gray-900/30 rounded-xl border border-dashed border-gray-800">
          <p className="text-gray-400 text-sm">No value bets selected yet.</p>
          <p className="text-gray-500 text-xs mt-1">
            Tap &quot;Select&quot; or &quot;Stake&quot; on any match card to calculate your optimal Naira stake.
          </p>
        </div>
      ) : (
        <div className="space-y-2 mb-6">
          <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">
            Optimal Stake Breakdown per Pick:
          </h3>
          {calculatedAllocations.map((item, idx) => (
            <div
              key={idx}
              className="bg-gray-900/80 border border-gray-800 p-3 rounded-xl flex flex-wrap justify-between items-center gap-3 hover:border-gray-700 transition-colors"
            >
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-extrabold text-sm text-white">{item.market_name}</span>
                  <span className="bg-emerald-950 text-emerald-400 text-[10px] font-bold px-1.5 py-0.5 rounded border border-emerald-500/40">
                    +{item.expected_value_pct.toFixed(1)}% EV
                  </span>
                </div>
                <p className="text-xs text-gray-400 mt-0.5">
                  Best odds on <b className="text-white">{item.bookmaker}</b>: <b className="text-emerald-400 font-mono">{item.market_odds.toFixed(2)}</b> (AI Fair Odds: {item.fair_odds.toFixed(2)})
                </p>
              </div>

              <div className="flex items-center gap-4">
                <div className="text-right">
                  <div className="text-sm font-black text-emerald-400 font-mono">
                    ₦{item.final_stake.toLocaleString()}
                  </div>
                  <div className="text-[10px] text-gray-400">
                    Payout: ₦{item.potential_payout.toLocaleString()} ({item.stake_pct}%)
                  </div>
                </div>

                <button
                  onClick={() => onRemoveBet(idx)}
                  className="text-gray-500 hover:text-red-400 p-1 transition-colors"
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
        <div className="flex flex-wrap justify-between items-center gap-3 pt-4 border-t border-gray-800">
          <p className="text-xs text-gray-400">
            Ready to place on SportyBet or Bet9ja?
          </p>

          <button
            onClick={onGenerateBookingSlip}
            className="w-full sm:w-auto bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-400 hover:to-emerald-500 text-black font-extrabold px-6 py-2.5 rounded-xl shadow-lg flex items-center justify-center gap-2 text-sm glow-emerald"
          >
            <span>Generate SportyBet & Bet9ja Codes</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  );
}
