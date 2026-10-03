"use client";

import React, { useMemo, useState } from "react";
import { CheckCircle2, Clock, XCircle } from "lucide-react";
import { PastMatch } from "@/types";
import Crest from "@/components/ui/Crest";
import Chip from "@/components/ui/Chip";
import GlassCard from "@/components/ui/GlassCard";
import Reveal from "@/components/motion/Reveal";
import PredictionStrip from "@/components/records/PredictionStrip";

type Filter = "all" | "correct" | "incorrect" | "awaiting";
const PAGE = 20;

const outcomeText = (m: PastMatch, o: "1" | "X" | "2") => (o === "1" ? `${m.home_team} win` : o === "2" ? `${m.away_team} win` : "Draw");
const dateText = (iso: string) => new Date(iso).toLocaleDateString(undefined, { weekday: "short", day: "numeric", month: "short" });

function Verdict({ m }: { m: PastMatch }) {
  if (m.correct === true) return <Chip tone="success" pill><CheckCircle2 className="h-3 w-3" />Correct</Chip>;
  if (m.correct === false) return <Chip tone="caution" pill><XCircle className="h-3 w-3" />Incorrect</Chip>;
  return <Chip tone="neutral" pill><Clock className="h-3 w-3" />Awaiting result</Chip>;
}

function PastRow({ m }: { m: PastMatch }) {
  const hasScore = m.home_goals != null && m.away_goals != null;
  return (
    <GlassCard>
      <div className="grid gap-3 p-3 md:grid-cols-[8.5rem_minmax(0,1.2fr)_minmax(0,1.1fr)_9rem_8.5rem] md:items-center md:gap-4">
        <div className="flex items-center justify-between gap-2 md:block">
          <div className="min-w-0">
            <p className="font-mono text-[11px] font-semibold text-slate-700 dark:text-gray-200">{dateText(m.kickoff_utc)}</p>
            <p className="truncate font-mono text-[10px] uppercase tracking-wide text-slate-500 dark:text-gray-400">{m.league}</p>
          </div>
          <span className="shrink-0 md:hidden"><Verdict m={m} /></span>
        </div>

        <div className="min-w-0 space-y-1.5">
          {[{ name: m.home_team, crest: m.home_crest }, { name: m.away_team, crest: m.away_crest }].map((t) => (
            <div key={t.name} className="flex min-w-0 items-center gap-2">
              <Crest src={t.crest} name={t.name} size={22} />
              <span className="truncate text-sm font-semibold text-slate-900 dark:text-white" title={t.name}>{t.name}</span>
            </div>
          ))}
        </div>

        <div>
          <p className="mb-1 text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-gray-400">AI predicted: {outcomeText(m, m.pick)}</p>
          <PredictionStrip p_home={m.p_home} p_draw={m.p_draw} p_away={m.p_away} pick={m.pick} actual={m.actual} />
        </div>

        <div className="md:text-center">
          <p className="mb-1 text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-gray-400 md:hidden">Actual result</p>
          {hasScore ? (
            <>
              <p className="font-mono text-2xl font-bold leading-none text-slate-900 dark:text-white">{m.home_goals} - {m.away_goals}</p>
              <p className="mt-1 text-[11px] text-slate-500 dark:text-gray-400">
                {m.actual ? outcomeText(m, m.actual) : "Full time"}
                {m.provisional && <span className="text-amber-500"> · unconfirmed</span>}
              </p>
            </>
          ) : (
            <p className="text-xs text-slate-500 dark:text-gray-400">Result not in yet</p>
          )}
        </div>

        <div className="hidden md:flex md:justify-center"><Verdict m={m} /></div>
      </div>
    </GlassCard>
  );
}

export default function PastMatches({ matches, summary }: { matches: PastMatch[]; summary: { graded: number; correct: number; accuracy_pct: number } }) {
  const [filter, setFilter] = useState<Filter>("all");
  const [shown, setShown] = useState(PAGE);

  const rows = useMemo(() => {
    switch (filter) {
      case "correct": return matches.filter((m) => m.correct === true);
      case "incorrect": return matches.filter((m) => m.correct === false);
      case "awaiting": return matches.filter((m) => m.status === "awaiting");
      default: return matches;
    }
  }, [matches, filter]);

  const filters: { key: Filter; label: string }[] = [
    { key: "all", label: "All" }, { key: "correct", label: "Correct" },
    { key: "incorrect", label: "Incorrect" }, { key: "awaiting", label: "Awaiting" },
  ];

  return (
    <section aria-labelledby="past-heading" className="mb-8">
      <div className="mb-3 flex flex-wrap items-end justify-between gap-2">
        <div>
          <h3 id="past-heading" className="font-display text-base font-semibold text-slate-900 dark:text-white">Past matches: AI prediction vs result</h3>
          <p className="text-xs text-slate-500 dark:text-gray-400">
            {summary.graded > 0
              ? `The model's top pick was right in ${summary.correct} of ${summary.graded} confirmed results (${summary.accuracy_pct}%).`
              : "No confirmed results yet."}
          </p>
        </div>
        <div className="flex flex-wrap gap-1.5" role="group" aria-label="Filter past matches">
          {filters.map((f) => (
            <button
              key={f.key}
              onClick={() => { setFilter(f.key); setShown(PAGE); }}
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

      {rows.length === 0 ? (
        <p className="rounded-panel border border-dashed border-slate-300 p-5 text-center text-xs text-slate-500 dark:border-white/[0.12] dark:text-gray-400">
          {matches.length === 0 ? "Nothing to show yet. Results appear here after full time." : "No matches for this filter."}
        </p>
      ) : (
        <div className="space-y-2.5">
          {rows.slice(0, shown).map((m) => (
            <Reveal key={m.id} y={14}>
              <PastRow m={m} />
            </Reveal>
          ))}
          {rows.length > shown && (
            <button
              onClick={() => setShown((n) => n + PAGE)}
              className="w-full rounded-lg border border-slate-200 py-2 text-xs font-bold text-slate-700 hover:bg-slate-100 dark:border-white/[0.08] dark:text-gray-200 dark:hover:bg-slate-800"
            >
              Show more ({rows.length - shown} left)
            </button>
          )}
        </div>
      )}
    </section>
  );
}
