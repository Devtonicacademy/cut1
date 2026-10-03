"use client";

import React from "react";
import { ModelReport } from "@/types";
import { BarChart2, Target, Scale } from "lucide-react";

interface AccuracyViewProps {
  report: ModelReport | null;
}

const PREDICTORS: { key: string; label: string; ours?: boolean }[] = [
  { key: "model_with_market", label: "LivelyBorg: football data + bookmaker odds", ours: true },
  { key: "model_football_only", label: "LivelyBorg: football data only", ours: true },
  { key: "bookmakers_pre_match_avg", label: "Bookmakers (average odds, pre-match)" },
  { key: "bookmakers_closing_avg", label: "Bookmakers (average odds, at kickoff)" },
  { key: "always_home", label: "Always pick the home team" },
];

const LEAGUE_NAMES: Record<string, string> = {
  E0: "Premier League", SP1: "La Liga", I1: "Serie A", D1: "Bundesliga", F1: "Ligue 1",
};

const pct = (x: number) => `${(x * 100).toFixed(1)}%`;
const season = (code: string) => `20${code.slice(0, 2)}/${code.slice(2)}`;

export default function AccuracyView({ report }: AccuracyViewProps) {
  if (!report) {
    return (
      <div className="max-w-4xl mx-auto text-center py-12 text-sm text-slate-500 dark:text-gray-400">
        The accuracy report is not available right now.
      </div>
    );
  }

  const testN = report.test.model_with_market?.n ?? 0;
  const primary = report.variants[report.primary_variant];

  return (
    <div className="bg-white dark:bg-[#111827] border border-slate-200 dark:border-gray-800 rounded-2xl p-4 sm:p-6 shadow-sm max-w-4xl mx-auto space-y-6">
      <div className="border-b border-slate-200 dark:border-gray-800 pb-4">
        <h2 className="text-base sm:text-xl font-black text-slate-900 dark:text-white flex items-center gap-2">
          <BarChart2 className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
          <span>How accurate are our predictions?</span>
        </h2>
        <p className="text-xs text-slate-500 dark:text-gray-400 mt-1 leading-relaxed">
          Tested on <b>{testN.toLocaleString()}</b> matches from {report.splits.test.map(season).join(" and ")} across 22
          leagues, which the model never saw while learning. It was trained on {primary?.matches_used.toLocaleString()} earlier
          matches (last update {new Date(report.trained_at).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" })}).
        </p>
      </div>

      <div className="bg-slate-50 dark:bg-gray-900/60 border border-slate-200 dark:border-gray-800 rounded-lg p-3 text-xs text-slate-600 dark:text-gray-300 leading-relaxed">
        Football is unpredictable: even bookmakers pick the right result only about half the time. What matters is
        whether our percentages are honest: when we say 70%, it should happen about 7 times in 10.
      </div>

      {/* Head-to-head comparison */}
      <section className="space-y-2">
        <h3 className="text-xs font-bold text-slate-500 dark:text-gray-400 uppercase tracking-wider flex items-center gap-1.5">
          <Target className="w-3.5 h-3.5" /> Compared with the bookmakers
        </h3>
        <div className="overflow-x-auto rounded-lg border border-slate-200 dark:border-gray-800">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-100 dark:bg-gray-900/90 text-slate-600 dark:text-gray-400 text-[10px] uppercase">
              <tr>
                <th className="p-2.5">Predictor</th>
                <th className="p-2.5 text-right">Correct result</th>
                <th className="p-2.5 text-right" title="Log loss: how far the percentages were from what happened">
                  Probability error (lower is better)
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 dark:divide-gray-800">
              {PREDICTORS.filter((p) => report.test[p.key]).map((p) => {
                const s = report.test[p.key];
                return (
                  <tr key={p.key} className={p.ours ? "bg-emerald-50/70 dark:bg-emerald-950/20 font-bold" : ""}>
                    <td className="p-2.5 text-slate-800 dark:text-gray-200">{p.label}</td>
                    <td className="p-2.5 text-right font-mono">{pct(s.accuracy)}</td>
                    <td className="p-2.5 text-right font-mono">{p.key === "always_home" ? "n/a" : s.log_loss.toFixed(4)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

      {/* Calibration */}
      <section className="space-y-2">
        <h3 className="text-xs font-bold text-slate-500 dark:text-gray-400 uppercase tracking-wider flex items-center gap-1.5">
          <Scale className="w-3.5 h-3.5" /> Do our percentages come true?
        </h3>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
          {report.test_calibration.map((row) => (
            <div key={row.bucket} className="bg-slate-50 dark:bg-[#1E293B] border border-slate-200 dark:border-gray-800 rounded-lg p-3 text-center">
              <span className="text-[10px] uppercase font-bold text-slate-500 dark:text-gray-400">Picks rated {row.bucket}</span>
              <p className="text-xs text-slate-600 dark:text-gray-300 mt-1">We said <b>{pct(row.predicted)}</b></p>
              <p className="text-lg font-black text-emerald-600 dark:text-emerald-400 font-mono">{pct(row.actual)}</p>
              <span className="text-[10px] text-slate-500 dark:text-gray-400">actually won ({row.matches.toLocaleString()} matches)</span>
            </div>
          ))}
        </div>
      </section>

      {/* Top leagues */}
      <section className="space-y-2">
        <h3 className="text-xs font-bold text-slate-500 dark:text-gray-400 uppercase tracking-wider">Top leagues</h3>
        <div className="overflow-x-auto rounded-lg border border-slate-200 dark:border-gray-800">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-100 dark:bg-gray-900/90 text-slate-600 dark:text-gray-400 text-[10px] uppercase">
              <tr>
                <th className="p-2.5">League</th>
                <th className="p-2.5 text-right">LivelyBorg correct</th>
                <th className="p-2.5 text-right">Bookmakers correct</th>
                <th className="p-2.5 text-right">Matches</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 dark:divide-gray-800">
              {Object.entries(report.test_top_leagues).map(([div, scores]) => (
                <tr key={div}>
                  <td className="p-2.5 font-semibold text-slate-800 dark:text-gray-200">{LEAGUE_NAMES[div] ?? div}</td>
                  <td className="p-2.5 text-right font-mono">{pct(scores.model_with_market.accuracy)}</td>
                  <td className="p-2.5 text-right font-mono">{pct(scores.bookmakers.accuracy)}</td>
                  <td className="p-2.5 text-right font-mono">{scores.bookmakers.n}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="text-xs text-slate-600 dark:text-gray-300 bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900/50 rounded-lg p-3 leading-relaxed">
        <b>Value bets:</b>{" "}
        {report.value_policy.enabled
          ? `switched on. Backing picks with at least +${((report.value_policy.min_ev ?? 0) * 100).toFixed(0)}% estimated edge was profitable in both test periods.`
          : "switched off. Backing our \"edges\" against the bookmakers did not make a profit in testing, so we don't recommend stakes. We show predictions only."}
      </section>
    </div>
  );
}
