"use client";

import React from "react";
import { ChainVerification, TrackRecordStats } from "@/types";
import { ShieldCheck, ShieldAlert, Award, CheckCircle2, XCircle } from "lucide-react";
import { useTrackMatches } from "@/components/records/useTrackMatches";
import OngoingMatches from "@/components/records/OngoingMatches";
import PastMatches from "@/components/records/PastMatches";

interface TrackRecordViewProps {
  stats: TrackRecordStats | null;
  verification: ChainVerification | null;
}

const signedNaira = (x: number) => `${x < 0 ? "-" : "+"}₦${Math.abs(x).toLocaleString()}`;
const signedPct = (x: number) => `${x < 0 ? "" : "+"}${x.toFixed(1)}%`;

export default function TrackRecordView({ stats, verification }: TrackRecordViewProps) {
  const { data: matches, failed, reload } = useTrackMatches();
  if (!stats) return null;
  const graded = stats.wins + stats.losses;

  return (
    <div className="bg-white dark:bg-[#111827] border border-slate-200 dark:border-gray-800 rounded-2xl p-4 sm:p-6 shadow-sm max-w-5xl mx-auto transition-colors duration-150">
      {/* Header */}
      <div className="flex flex-wrap justify-between items-center gap-3 border-b border-slate-200 dark:border-gray-800 pb-4 mb-6">
        <div>
          <h2 className="text-base sm:text-xl font-black text-slate-900 dark:text-white flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
            <span>Public Track Record</span>
          </h2>
          <p className="text-xs text-slate-500 dark:text-gray-400 mt-0.5">
            Every prediction is locked before kickoff, graded automatically from official results, and sealed in a hash chain so no past pick can be edited or deleted unnoticed.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {verification && (
            <div
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-bold border ${
                verification.valid
                  ? "bg-emerald-50 dark:bg-emerald-950/60 border-emerald-300 dark:border-emerald-500/40 text-emerald-800 dark:text-emerald-300"
                  : "bg-rose-50 dark:bg-red-950/40 border-rose-300 dark:border-red-500/40 text-rose-800 dark:text-red-300"
              }`}
              title={verification.latest_hash ? `Latest hash: ${verification.latest_hash}` : undefined}
            >
              {verification.valid ? <ShieldCheck className="w-4 h-4" /> : <ShieldAlert className="w-4 h-4" />}
              <span>{verification.valid ? `Hash chain verified (${verification.entries} entries)` : "Hash chain broken"}</span>
            </div>
          )}
          <div className="flex items-center gap-2 bg-slate-50 dark:bg-gray-900/60 border border-slate-200 dark:border-gray-700 px-3 py-1.5 rounded-full text-xs font-bold text-slate-700 dark:text-gray-300">
            <Award className="w-4 h-4 text-amber-500" />
            <span>Current streak: {stats.current_winning_streak}</span>
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 sm:gap-3 mb-6">
        <div className="bg-slate-50 dark:bg-[#1E293B] p-3 rounded-lg border border-slate-200 dark:border-gray-800 text-center">
          <span className="text-[10px] text-slate-500 dark:text-gray-400 uppercase font-bold">Correct picks</span>
          <p className="text-xl sm:text-2xl font-black text-emerald-600 dark:text-emerald-400 font-mono mt-0.5">
            {stats.win_rate_pct.toFixed(1)}%
          </p>
          <span className="text-[10px] text-slate-500 dark:text-gray-400">{stats.wins} Won / {stats.losses} Lost</span>
        </div>

        <div className="bg-slate-50 dark:bg-[#1E293B] p-3 rounded-lg border border-slate-200 dark:border-gray-800 text-center">
          <span className="text-[10px] text-slate-500 dark:text-gray-400 uppercase font-bold">Return (flat ₦1,000)</span>
          <p className="text-xl sm:text-2xl font-black text-amber-600 dark:text-gold-400 font-mono mt-0.5">
            {signedPct(stats.roi_pct)}
          </p>
          <span className="text-[10px] text-slate-500 dark:text-gray-400">if you staked ₦1,000 on every priced pick</span>
        </div>

        <div className="bg-slate-50 dark:bg-[#1E293B] p-3 rounded-lg border border-slate-200 dark:border-gray-800 text-center">
          <span className="text-[10px] text-slate-500 dark:text-gray-400 uppercase font-bold">Net result</span>
          <p className="text-xl sm:text-2xl font-black text-slate-900 dark:text-white font-mono mt-0.5">
            {signedNaira(stats.net_profit_ngn)}
          </p>
          <span className="text-[10px] text-slate-500 dark:text-gray-400">Return: ₦{stats.total_returned_ngn.toLocaleString()}</span>
        </div>

        <div className="bg-slate-50 dark:bg-[#1E293B] p-3 rounded-lg border border-slate-200 dark:border-gray-800 text-center">
          <span className="text-[10px] text-slate-500 dark:text-gray-400 uppercase font-bold">Predictions</span>
          <p className="text-xl sm:text-2xl font-black text-blue-600 dark:text-blue-300 font-mono mt-0.5">
            {stats.total_bets}
          </p>
          <span className="text-[10px] text-slate-500 dark:text-gray-400">{graded} graded • {stats.total_bets - graded - stats.voids} pending</span>
        </div>
      </div>

      {/* Matches in play and results, next to the prediction locked for each */}
      {matches ? (
        <>
          <OngoingMatches matches={matches.ongoing} />
          <PastMatches matches={matches.past} summary={matches.summary} />
        </>
      ) : (
        <p className="mb-8 text-center text-xs text-slate-500 dark:text-gray-400">
          {failed ? (
            <>Could not load match results. <button onClick={reload} className="font-bold text-emerald-500 hover:underline">Try again</button></>
          ) : (
            "Loading matches…"
          )}
        </p>
      )}

      {/* Historical Ledger Table */}
      <h3 className="mb-1 font-display text-base font-semibold text-slate-900 dark:text-white">Full ledger</h3>
      <p className="mb-3 text-xs text-slate-500 dark:text-gray-400">Every locked prediction with the odds, the notional ₦1,000 stake and its return.</p>
      <div className="overflow-x-auto rounded-lg border border-slate-200 dark:border-gray-800">
        <table className="w-full text-left text-xs text-slate-700 dark:text-gray-300">
          <thead className="bg-slate-100 dark:bg-gray-900/90 text-slate-600 dark:text-gray-400 font-bold uppercase text-[10px] border-b border-slate-200 dark:border-gray-800">
            <tr>
              <th className="p-3">Date & Match</th>
              <th className="p-3">Prediction</th>
              <th className="p-3">Odds</th>
              <th className="p-3">Notional stake</th>
              <th className="p-3">Result</th>
              <th className="p-3">Result (₦)</th>
              <th className="p-3">Details</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 dark:divide-gray-800/80 bg-white dark:bg-[#0B0F19]/60">
            {stats.entries.length === 0 && (
              <tr>
                <td colSpan={7} className="p-4 text-center text-slate-500 dark:text-gray-400">
                  No predictions locked yet. Each match&apos;s prediction is locked in the 36 hours before kickoff.
                </td>
              </tr>
            )}
            {stats.entries.map((entry) => (
              <tr key={entry.id} className="hover:bg-slate-50 dark:hover:bg-gray-800/40 transition-colors">
                <td className="p-3">
                  <span className="font-bold text-slate-900 dark:text-white block">{entry.match}</span>
                  <span className="text-[10px] text-slate-500 dark:text-gray-400 font-mono">{entry.date}</span>
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
                  ) : entry.result === "lost" ? (
                    <span className="inline-flex items-center gap-1 bg-rose-100 dark:bg-red-500/20 text-rose-800 dark:text-red-400 border border-rose-300 dark:border-red-500/30 text-[10px] font-bold px-2 py-0.5 rounded">
                      <XCircle className="w-3 h-3" />
                      <span>LOST</span>
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 bg-slate-100 dark:bg-gray-700/40 text-slate-700 dark:text-gray-300 border border-slate-300 dark:border-gray-600 text-[10px] font-bold px-2 py-0.5 rounded">
                      <span>{entry.result === "void" ? "VOID" : "PENDING"}</span>
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
                  {entry.ai_post_mortem}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
