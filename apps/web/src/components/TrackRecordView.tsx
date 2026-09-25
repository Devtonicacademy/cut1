"use client";

import React from "react";
import { TrackRecordStats } from "@/types";
import { ShieldCheck, TrendingUp, Award, CheckCircle2, XCircle } from "lucide-react";

interface TrackRecordViewProps {
  stats: TrackRecordStats | null;
}

export default function TrackRecordView({ stats }: TrackRecordViewProps) {
  if (!stats) return null;

  return (
    <div className="bg-white dark:bg-[#0d1322] border border-slate-200 dark:border-gray-800 rounded-2xl p-4 sm:p-6 shadow-sm max-w-5xl mx-auto transition-colors duration-150">
      {/* Header */}
      <div className="flex flex-wrap justify-between items-center gap-3 border-b border-slate-200 dark:border-gray-800 pb-4 mb-6">
        <div>
          <h2 className="text-base sm:text-xl font-black text-slate-900 dark:text-white flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
            <span>Public Audited Track Record & Verified ROI</span>
          </h2>
          <p className="text-xs text-slate-500 dark:text-gray-400 mt-0.5">
            Zero deleted slips. Zero edited tickets. Every prediction is permanently timestamped before kickoff.
          </p>
        </div>

        <div className="flex items-center gap-2 bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-300 dark:border-emerald-500/40 px-3 py-1.5 rounded-full text-xs font-bold text-emerald-800 dark:text-emerald-300">
          <Award className="w-4 h-4 text-amber-500" />
          <span>Current Streak: {stats.current_winning_streak} Wins in a Row</span>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 sm:gap-3 mb-6">
        <div className="bg-slate-50 dark:bg-[#11192e] p-3 rounded-xl border border-slate-200 dark:border-gray-800 text-center">
          <span className="text-[10px] text-slate-500 dark:text-gray-400 uppercase font-bold">Win Rate</span>
          <p className="text-xl sm:text-2xl font-black text-emerald-600 dark:text-emerald-400 font-mono mt-0.5">
            {stats.win_rate_pct.toFixed(1)}%
          </p>
          <span className="text-[10px] text-slate-500 dark:text-gray-400">{stats.wins} Won / {stats.losses} Lost</span>
        </div>

        <div className="bg-slate-50 dark:bg-[#11192e] p-3 rounded-xl border border-slate-200 dark:border-gray-800 text-center">
          <span className="text-[10px] text-slate-500 dark:text-gray-400 uppercase font-bold">Audited ROI</span>
          <p className="text-xl sm:text-2xl font-black text-amber-600 dark:text-gold-400 font-mono mt-0.5">
            +{stats.roi_pct.toFixed(1)}%
          </p>
          <span className="text-[10px] text-slate-500 dark:text-gray-400">Yield on capital</span>
        </div>

        <div className="bg-slate-50 dark:bg-[#11192e] p-3 rounded-xl border border-slate-200 dark:border-gray-800 text-center">
          <span className="text-[10px] text-slate-500 dark:text-gray-400 uppercase font-bold">Total Net Profit</span>
          <p className="text-xl sm:text-2xl font-black text-slate-900 dark:text-white font-mono mt-0.5">
            +₦{stats.net_profit_ngn.toLocaleString()}
          </p>
          <span className="text-[10px] text-slate-500 dark:text-gray-400">Return: ₦{stats.total_returned_ngn.toLocaleString()}</span>
        </div>

        <div className="bg-slate-50 dark:bg-[#11192e] p-3 rounded-xl border border-slate-200 dark:border-gray-800 text-center">
          <span className="text-[10px] text-slate-500 dark:text-gray-400 uppercase font-bold">Total Staked</span>
          <p className="text-xl sm:text-2xl font-black text-blue-600 dark:text-blue-300 font-mono mt-0.5">
            ₦{stats.total_staked_ngn.toLocaleString()}
          </p>
          <span className="text-[10px] text-slate-500 dark:text-gray-400">{stats.total_bets} verified wagers</span>
        </div>
      </div>

      {/* Historical Ledger Table */}
      <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-gray-800">
        <table className="w-full text-left text-xs text-slate-700 dark:text-gray-300">
          <thead className="bg-slate-100 dark:bg-gray-900/90 text-slate-600 dark:text-gray-400 font-bold uppercase text-[10px] border-b border-slate-200 dark:border-gray-800">
            <tr>
              <th className="p-3">Date & Match</th>
              <th className="p-3">Prediction</th>
              <th className="p-3">Odds</th>
              <th className="p-3">Stake</th>
              <th className="p-3">Result</th>
              <th className="p-3">Profit (₦)</th>
              <th className="p-3">AI Post-Mortem Analysis</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 dark:divide-gray-800/80 bg-white dark:bg-[#0a0f1c]/60">
            {stats.entries.map((entry) => (
              <tr key={entry.id} className="hover:bg-slate-50 dark:hover:bg-gray-800/40 transition-colors">
                <td className="p-3">
                  <span className="font-bold text-slate-900 dark:text-white block">{entry.match}</span>
                  <span className="text-[10px] text-slate-400 dark:text-gray-500 font-mono">{entry.date}</span>
                </td>
                <td className="p-3 font-semibold text-emerald-700 dark:text-emerald-300">{entry.prediction}</td>
                <td className="p-3 font-mono font-bold">{entry.odds.toFixed(2)}</td>
                <td className="p-3 font-mono">₦{entry.stake_ngn.toLocaleString()}</td>
                <td className="p-3">
                  {entry.result === "won" ? (
                    <span className="inline-flex items-center gap-1 bg-emerald-100 dark:bg-emerald-500/20 text-emerald-800 dark:text-emerald-400 border border-emerald-300 dark:border-emerald-500/30 text-[10px] font-bold px-2 py-0.5 rounded">
                      <CheckCircle2 className="w-3 h-3" />
                      <span>WON</span>
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 bg-rose-100 dark:bg-red-500/20 text-rose-800 dark:text-red-400 border border-rose-300 dark:border-red-500/30 text-[10px] font-bold px-2 py-0.5 rounded">
                      <XCircle className="w-3 h-3" />
                      <span>LOST</span>
                    </span>
                  )}
                </td>
                <td className="p-3 font-mono font-bold">
                  {entry.profit_ngn >= 0 ? (
                    <span className="text-emerald-600 dark:text-emerald-400">+₦{entry.profit_ngn.toLocaleString()}</span>
                  ) : (
                    <span className="text-rose-600 dark:text-red-400">-₦{Math.abs(entry.profit_ngn).toLocaleString()}</span>
                  )}
                </td>
                <td className="p-3 text-[11px] text-slate-500 dark:text-gray-400 max-w-xs leading-relaxed">
                  {entry.ai_post_mortem || "Statistically verified wager"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
