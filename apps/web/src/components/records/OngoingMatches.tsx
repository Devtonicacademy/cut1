"use client";

import React from "react";
import { OngoingMatch } from "@/types";
import Crest from "@/components/ui/Crest";
import GlassCard from "@/components/ui/GlassCard";
import Reveal, { staggerDelay } from "@/components/motion/Reveal";
import PredictionStrip from "@/components/records/PredictionStrip";

/** Pulsing red badge so a match in play is unmistakable. */
export function OngoingBadge() {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full border border-rose-500/40 bg-rose-500/[0.12] px-2.5 py-0.5 font-mono text-[11px] font-bold uppercase tracking-wide text-rose-500">
      <span className="relative flex h-2 w-2">
        <span className="absolute inline-flex h-full w-full rounded-full bg-rose-500 opacity-75 motion-safe:animate-ping" />
        <span className="relative inline-flex h-2 w-2 rounded-full bg-rose-500" />
      </span>
      Ongoing
    </span>
  );
}

function clock(m: OngoingMatch): string {
  if (m.live_status === "PAUSED") return "Half-time";
  if (m.live_status && m.minute != null) return `${m.minute}'`;
  return `Kicked off ${m.minutes_since_kickoff} min ago`;
}

function OngoingCard({ m }: { m: OngoingMatch }) {
  const hasScore = m.home_goals != null && m.away_goals != null;
  return (
    <GlassCard className="flex h-full flex-col">
      <div className="flex flex-1 flex-col gap-4 p-4">
        <div className="flex items-center justify-between gap-2">
          <OngoingBadge />
          <span className="truncate font-mono text-[10px] uppercase tracking-wider text-slate-500 dark:text-gray-400">{m.league}</span>
        </div>

        <div className="grid grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] items-start gap-2">
          {[{ name: m.home_team, crest: m.home_crest }, null, { name: m.away_team, crest: m.away_crest }].map((side, i) =>
            side ? (
              <div key={i} className="flex min-w-0 flex-col items-center gap-1.5 text-center">
                <Crest src={side.crest} name={side.name} size={40} />
                <span className="line-clamp-2 [overflow-wrap:anywhere] font-display text-sm font-semibold leading-tight text-slate-900 dark:text-white">{side.name}</span>
              </div>
            ) : (
              <div key={i} className="flex flex-col items-center gap-1 pt-1 text-center" aria-live="polite">
                <span className="font-mono text-3xl font-bold leading-none text-slate-900 dark:text-white">
                  {hasScore ? `${m.home_goals} - ${m.away_goals}` : "- : -"}
                </span>
                <span className="font-mono text-[11px] font-semibold text-rose-500">{clock(m)}</span>
              </div>
            ),
          )}
        </div>

        <div>
          <p className="mb-1 text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-gray-400">AI prediction (locked before kickoff)</p>
          <PredictionStrip p_home={m.p_home} p_draw={m.p_draw} p_away={m.p_away} pick={m.pick} />
        </div>

        {!hasScore && (
          <p className="mt-auto text-[11px] leading-relaxed text-slate-500 dark:text-gray-400">
            Live score not available right now. The final result is confirmed from official data after full time.
          </p>
        )}
      </div>
    </GlassCard>
  );
}

export default function OngoingMatches({ matches }: { matches: OngoingMatch[] }) {
  return (
    <section aria-labelledby="ongoing-heading" className="mb-8">
      <div className="mb-3 flex items-center gap-2">
        <h3 id="ongoing-heading" className="font-display text-base font-semibold text-slate-900 dark:text-white">Ongoing matches</h3>
        {matches.length > 0 && (
          <span className="rounded-chip border border-rose-500/30 px-1.5 font-mono text-[10px] font-semibold text-rose-500">{matches.length}</span>
        )}
      </div>
      {matches.length === 0 ? (
        <p className="rounded-panel border border-dashed border-slate-300 p-5 text-center text-xs text-slate-500 dark:border-white/[0.12] dark:text-gray-400">
          No matches in play right now. Matches appear here from kickoff and move to Past matches once the result is in.
        </p>
      ) : (
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
          {matches.map((m, i) => (
            <Reveal key={m.id} delay={staggerDelay(i % 3)}>
              <OngoingCard m={m} />
            </Reveal>
          ))}
        </div>
      )}
    </section>
  );
}
