"use client";

import React, { useCallback, useEffect, useMemo, useState } from "react";
import { CheckCircle2, Clock, RefreshCw, ShieldCheck, XCircle } from "lucide-react";
import { apiJson, useAuth } from "@/lib/auth";
import { PredictionReport } from "@/types";
import GlassCard from "@/components/ui/GlassCard";
import Chip from "@/components/ui/Chip";
import Reveal from "@/components/motion/Reveal";

type Filter = "all" | "correct" | "wrong" | "pending";
const OUTCOME_LABEL = { "1": "Home win", X: "Draw", "2": "Away win" } as const;

function Kpi({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <GlassCard className="p-4">
      <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-gray-400">{label}</p>
      <p className="mt-1 font-mono text-2xl font-bold text-slate-900 dark:text-white">{value}</p>
      {hint && <p className="mt-0.5 text-[11px] text-slate-500 dark:text-gray-400">{hint}</p>}
    </GlassCard>
  );
}

/** Admin-only: the AI's locked predictions set against what actually happened. */
export default function AdminView() {
  const { ready, user, openSignIn } = useAuth();
  const [report, setReport] = useState<PredictionReport | null>(null);
  const [state, setState] = useState<"loading" | "ok" | "forbidden" | "error">("loading");
  const [filter, setFilter] = useState<Filter>("all");

  const load = useCallback(async () => {
    setState("loading");
    const res = await apiJson<PredictionReport>("/admin/reports/predictions?limit=500");
    if (res.data) {
      setReport(res.data);
      setState("ok");
    } else {
      setState(res.status === 401 || res.status === 403 ? "forbidden" : "error");
    }
  }, []);

  useEffect(() => {
    if (ready && user?.role === "admin") load();
  }, [ready, user, load]);

  const rows = useMemo(() => {
    const all = report?.matches ?? [];
    switch (filter) {
      case "correct": return all.filter((m) => m.correct === true);
      case "wrong": return all.filter((m) => m.correct === false);
      case "pending": return all.filter((m) => m.status === "pending");
      default: return all;
    }
  }, [report, filter]);

  if (ready && !user) {
    return (
      <div className="mx-auto max-w-md py-16 text-center">
        <ShieldCheck className="mx-auto mb-3 h-8 w-8 text-amber-500" />
        <p className="mb-4 text-sm text-slate-600 dark:text-gray-400">Sign in with the admin account to see these reports.</p>
        <button onClick={openSignIn} className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-bold text-black hover:bg-emerald-400">Sign in</button>
      </div>
    );
  }
  if (ready && user && user.role !== "admin") {
    return <p className="py-16 text-center text-sm text-slate-600 dark:text-gray-400">This page is for administrators only.</p>;
  }
  if (state === "forbidden") return <p className="py-16 text-center text-sm text-slate-600 dark:text-gray-400">Your session does not have admin access.</p>;
  if (state === "error") {
    return (
      <div className="py-16 text-center text-sm text-slate-600 dark:text-gray-400">
        Could not load the report. <button onClick={load} className="font-bold text-emerald-500 hover:underline">Try again</button>
      </div>
    );
  }
  if (!report) return <p className="py-16 text-center text-sm text-slate-500 dark:text-gray-400">Loading report…</p>;

  const s = report.summary;
  const skill = s.baseline_brier > 0 ? (1 - s.brier / s.baseline_brier) * 100 : 0;
  const filters: { key: Filter; label: string }[] = [
    { key: "all", label: `All (${report.matches.length})` },
    { key: "correct", label: "Correct" },
    { key: "wrong", label: "Wrong" },
    { key: "pending", label: `Pending (${s.pending})` },
  ];

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-2">
        <div>
          <h2 className="flex items-center gap-2 font-display text-xl font-bold text-slate-900 dark:text-white">
            <ShieldCheck className="h-5 w-5 text-amber-500" /> Admin: predictions vs outcomes
          </h2>
          <p className="text-xs text-slate-600 dark:text-gray-400">
            Every prediction locked before kickoff, set against the final score. Updated {new Date(report.generated_at).toLocaleString()}.
          </p>
        </div>
        <button onClick={load} className="flex items-center gap-1.5 rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-bold text-slate-700 hover:bg-slate-100 dark:border-glass dark:text-gray-200 dark:hover:bg-slate-800">
          <RefreshCw className={`h-3.5 w-3.5 ${state === "loading" ? "animate-spin" : ""}`} /> Refresh
        </button>
      </div>

      <Reveal>
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          <Kpi label="Predictions locked" value={String(s.locked)} hint={`${s.graded} graded · ${s.pending} pending · ${s.voided} void`} />
          <Kpi label="Top-pick accuracy" value={s.graded ? `${s.accuracy_pct}%` : "n/a"} hint={`${s.correct} of ${s.graded} correct`} />
          <Kpi label="Avg confidence" value={s.graded ? `${s.avg_confidence_pct}%` : "n/a"} hint={s.graded ? `vs ${s.accuracy_pct}% actual` : undefined} />
          <Kpi
            label="Brier score"
            value={s.graded ? s.brier.toFixed(3) : "n/a"}
            hint={s.graded ? `${skill >= 0 ? "+" : ""}${skill.toFixed(1)}% vs naive (${s.baseline_brier.toFixed(3)}) · log loss ${s.log_loss.toFixed(3)}` : "lower is better"}
          />
        </div>
      </Reveal>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Reveal>
          <GlassCard className="h-full p-4">
            <h3 className="font-display text-sm font-semibold text-slate-900 dark:text-white">Calibration</h3>
            <p className="mb-3 text-[11px] text-slate-500 dark:text-gray-400">When the model gives its pick this chance, how often does it win?</p>
            <div className="space-y-2.5">
              {report.calibration.map((b) => (
                <div key={b.label} className="grid grid-cols-[4.5rem_1fr_3rem] items-center gap-2 text-[11px]">
                  <span className="font-mono text-slate-600 dark:text-gray-300">{b.label}</span>
                  {b.count === 0 ? (
                    <span className="text-slate-400">no matches yet</span>
                  ) : (
                    <div className="space-y-1">
                      <div className="h-2 rounded-full bg-slate-100 dark:bg-gray-800"><div className="h-2 rounded-full bg-blue-500" style={{ width: `${b.avg_predicted_pct}%` }} /></div>
                      <div className="h-2 rounded-full bg-slate-100 dark:bg-gray-800"><div className="h-2 rounded-full bg-emerald-500" style={{ width: `${b.actual_pct}%` }} /></div>
                    </div>
                  )}
                  <span className="text-right font-mono text-slate-500 dark:text-gray-400">n={b.count}</span>
                </div>
              ))}
            </div>
            <p className="mt-3 flex gap-3 text-[10px] text-slate-500 dark:text-gray-400">
              <span className="flex items-center gap-1"><i className="inline-block h-2 w-2 rounded-full bg-blue-500" />predicted</span>
              <span className="flex items-center gap-1"><i className="inline-block h-2 w-2 rounded-full bg-emerald-500" />actual</span>
            </p>
          </GlassCard>
        </Reveal>

        <Reveal delay={0.06}>
          <GlassCard className="h-full p-4">
            <h3 className="font-display text-sm font-semibold text-slate-900 dark:text-white">By league</h3>
            {report.leagues.length === 0 ? (
              <p className="mt-3 text-xs text-slate-500 dark:text-gray-400">No graded matches yet.</p>
            ) : (
              <table className="mt-2 w-full text-left text-xs">
                <thead className="text-[10px] uppercase text-slate-500 dark:text-gray-400">
                  <tr><th className="py-1 font-bold">League</th><th className="py-1 text-right font-bold">Graded</th><th className="py-1 text-right font-bold">Correct</th><th className="py-1 text-right font-bold">Accuracy</th></tr>
                </thead>
                <tbody className="font-mono text-slate-700 dark:text-gray-200">
                  {report.leagues.map((l) => (
                    <tr key={l.league} className="border-t border-slate-200 dark:border-white/[0.06]">
                      <td className="py-1.5 font-sans">{l.league}</td><td className="py-1.5 text-right">{l.graded}</td>
                      <td className="py-1.5 text-right">{l.correct}</td><td className="py-1.5 text-right font-bold">{l.accuracy_pct}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </GlassCard>
        </Reveal>
      </div>

      <Reveal>
        <GlassCard className="p-4">
          <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
            <h3 className="font-display text-sm font-semibold text-slate-900 dark:text-white">Match by match</h3>
            <div className="flex flex-wrap gap-1.5" role="group" aria-label="Filter matches">
              {filters.map((f) => (
                <button
                  key={f.key}
                  onClick={() => setFilter(f.key)}
                  aria-pressed={filter === f.key}
                  className={`rounded-chip border px-2.5 py-1 font-mono text-[11px] font-semibold ${
                    filter === f.key
                      ? "border-emerald-500/30 bg-emerald-500/[0.12] text-emerald-600 dark:text-emerald-500"
                      : "border-slate-200 text-slate-600 dark:border-white/[0.08] dark:text-gray-400"
                  }`}
                >
                  {f.label}
                </button>
              ))}
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[640px] text-left text-xs">
              <thead className="text-[10px] uppercase text-slate-500 dark:text-gray-400">
                <tr>
                  <th className="py-1.5 font-bold">Kick-off</th><th className="py-1.5 font-bold">Match</th>
                  <th className="py-1.5 font-bold">Predicted (1 / X / 2)</th><th className="py-1.5 font-bold">Pick</th>
                  <th className="py-1.5 font-bold">Actual</th><th className="py-1.5 text-center font-bold">Result</th>
                </tr>
              </thead>
              <tbody className="text-slate-700 dark:text-gray-200">
                {rows.length === 0 && <tr><td colSpan={6} className="py-6 text-center text-slate-500 dark:text-gray-400">No matches for this filter.</td></tr>}
                {rows.map((m) => (
                  <tr key={m.id} className="border-t border-slate-200 dark:border-white/[0.06]">
                    <td className="whitespace-nowrap py-2 font-mono text-[11px]">{new Date(m.kickoff_utc).toLocaleDateString(undefined, { day: "numeric", month: "short" })}</td>
                    <td className="py-2"><div className="font-semibold">{m.home_team} <span className="text-slate-400">vs</span> {m.away_team}</div><div className="text-[10px] text-slate-500 dark:text-gray-400">{m.league}</div></td>
                    <td className="whitespace-nowrap py-2 font-mono">
                      {[["1", m.p_home], ["X", m.p_draw], ["2", m.p_away]].map(([k, v]) => (
                        <span key={k as string} className={`mr-2 ${k === m.pick ? "font-bold text-emerald-600 dark:text-emerald-400" : "text-slate-500 dark:text-gray-400"}`}>
                          {Math.round((v as number) * 100)}%
                        </span>
                      ))}
                    </td>
                    <td className="py-2 font-mono font-bold">{m.pick}</td>
                    <td className="whitespace-nowrap py-2 font-mono">
                      {m.status === "graded" ? <>{m.home_goals}-{m.away_goals} <span className="text-slate-500 dark:text-gray-400">({OUTCOME_LABEL[m.actual!]})</span></> : <span className="text-slate-400">{m.status === "void" ? "void" : "not played"}</span>}
                    </td>
                    <td className="py-2 text-center">
                      {m.correct === true && <Chip tone="success" pill><CheckCircle2 className="h-3 w-3" />Right</Chip>}
                      {m.correct === false && <Chip tone="caution" pill><XCircle className="h-3 w-3" />Wrong</Chip>}
                      {m.correct === null && <Chip tone="neutral" pill><Clock className="h-3 w-3" />{m.status === "void" ? "Void" : "Pending"}</Chip>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </GlassCard>
      </Reveal>
    </div>
  );
}
