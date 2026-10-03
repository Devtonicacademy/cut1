"use client";

import React, { useState } from "react";
import { Bookmark, ChevronDown, Lightbulb } from "lucide-react";
import { useAuth } from "@/lib/auth";
import { Fixture, ValueBetItem } from "@/types";
import GlassCard from "@/components/ui/GlassCard";
import Chip from "@/components/ui/Chip";
import OddsText from "@/components/ui/OddsText";
import Crest from "@/components/ui/Crest";
import MatchDetailModal from "@/components/MatchDetailModal";

interface MatchCardProps {
  fixture: Fixture;
  onSelectBet: (bet: ValueBetItem, fixture: Fixture) => void;
  isSelected?: boolean;
  /** Larger treatment for the lead card of the bento grid. */
  featured?: boolean;
}

/** Splits the kick-off into a short date and a time, so the time can be the centrepiece of the card. */
function kickoffParts(f: Fixture): { date: string; time: string } {
  if (f.kickoff_timestamp) {
    const d = new Date(f.kickoff_timestamp);
    if (!Number.isNaN(d.getTime())) {
      return {
        date: d.toLocaleDateString(undefined, { weekday: "short", day: "numeric", month: "short" }),
        time: d.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit", hour12: false }),
      };
    }
  }
  if (f.match_date && f.match_time) return { date: f.match_date, time: f.match_time };
  return { date: "", time: f.kickoff };
}

/** Club-versus-club tile: home | kick-off | away, with each side's win probability under it. The rest lives behind "Why" and the detail modal. */
export default function MatchCard({ fixture, onSelectBet, isSelected, featured = false }: MatchCardProps) {
  const [whyOpen, setWhyOpen] = useState(false);
  const [detailOpen, setDetailOpen] = useState(false);
  const { savedIds, toggleSave } = useAuth();
  const saved = savedIds.has(fixture.id);
  const p = fixture.prediction;
  if (!p) return null;

  const whyId = `why-${fixture.id}`;
  const reasons =
    p.key_factors && p.key_factors.length > 0
      ? p.key_factors
      : p.statistical_verdict
      ? [p.statistical_verdict.split(/(?<=[.!?])\s/)[0]]
      : [];

  const kickoff = kickoffParts(fixture);
  const top = Math.max(p.prob_home_win, p.prob_draw, p.prob_away_win);
  const sides = [
    { team: fixture.home_team, p: p.prob_home_win },
    { team: fixture.away_team, p: p.prob_away_win },
  ];
  const teamSide = (side: (typeof sides)[number]) => (
    <div className="flex min-w-0 flex-col items-center gap-1.5 text-center">
      <Crest src={side.team.crest} name={side.team.name} size={featured ? 56 : 44} />
      <h3 className={teamName} title={side.team.name}>{side.team.name}</h3>
      <span className={prob(side.p === top)}>
        <OddsText value={side.p * 100} digits={0} suffix="%" />
      </span>
    </div>
  );
  // The likeliest outcome is emerald and bolder; the others stay muted.
  const prob = (isTop: boolean) =>
    `font-mono font-bold ${featured ? "text-2xl" : "text-xl"} ${isTop ? "text-emerald-600 dark:text-emerald-400" : "text-slate-500 dark:text-gray-400"}`;
  const teamName = `line-clamp-2 min-w-0 max-w-full [overflow-wrap:anywhere] font-display font-semibold leading-tight text-slate-900 dark:text-white ${featured ? "text-lg sm:text-xl" : "text-sm"}`;

  return (
    <>
      <GlassCard active={isSelected} className="flex h-full flex-col">
        <div className={`flex flex-1 flex-col gap-4 ${featured ? "p-5" : "p-4"}`}>
          <div className="flex items-center justify-between gap-2">
            <Chip tone="success" className="max-w-[75%] truncate uppercase tracking-wider">
              {fixture.league}
            </Chip>
            <button
              onClick={() => toggleSave(fixture.id)}
              aria-pressed={saved}
              aria-label={saved ? "Remove from my dashboard" : "Save to my dashboard"}
              title={saved ? "Saved: tap to remove" : "Save to my dashboard"}
              className={`rounded-lg p-1.5 transition-colors ${
                saved ? "text-emerald-500" : "text-slate-400 hover:bg-slate-100 hover:text-emerald-500 dark:hover:bg-slate-800"
              }`}
            >
              <Bookmark className={`h-4 w-4 ${saved ? "fill-current" : ""}`} />
            </button>
          </div>

          {/* Home | kick-off | away: one horizontal row, nothing stacked into a list */}
          <div className="grid grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] items-start gap-2">
            {teamSide(sides[0])}

            <div className="flex flex-col items-center gap-1 px-1 pt-1">
              {kickoff.date && <span className="font-mono text-[10px] uppercase tracking-wide text-slate-500 dark:text-gray-400">{kickoff.date}</span>}
              <span className={`font-mono font-bold leading-none text-slate-900 dark:text-white ${featured ? "text-3xl" : "text-2xl"}`}>{kickoff.time}</span>
              <span className="rounded-full border border-slate-200 px-2 py-0.5 text-[10px] font-black text-slate-500 dark:border-white/[0.12] dark:text-gray-400">VS</span>
              <span className={`font-mono text-[11px] ${p.prob_draw === top ? "font-bold text-emerald-600 dark:text-emerald-400" : "text-slate-500 dark:text-gray-400"}`}>
                Draw <OddsText value={p.prob_draw * 100} digits={0} suffix="%" />
              </span>
            </div>

            {teamSide(sides[1])}
          </div>

          <div className="flex h-2 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-gray-800" aria-hidden="true">
            <div style={{ width: `${p.prob_home_win * 100}%` }} className="bg-emerald-500" />
            <div style={{ width: `${p.prob_draw * 100}%` }} className="bg-slate-400 dark:bg-gray-600" />
            <div style={{ width: `${p.prob_away_win * 100}%` }} className="bg-blue-500" />
          </div>

          {/* "Why": collapsed by default */}
          <div className="mt-auto border-t border-slate-200 pt-2 dark:border-white/[0.08]">
            <button
              onClick={() => setWhyOpen((o) => !o)}
              aria-expanded={whyOpen}
              aria-controls={whyId}
              className="flex w-full items-center justify-between text-xs font-bold text-slate-700 dark:text-gray-200"
            >
              <span className="flex items-center gap-1.5">
                <Lightbulb className="h-3.5 w-3.5 text-amber-500" />
                Why
              </span>
              <ChevronDown className={`h-4 w-4 text-slate-500 transition-transform dark:text-gray-400 ${whyOpen ? "rotate-180" : ""}`} />
            </button>
            {whyOpen && (
              <div id={whyId} className="mt-2 space-y-2 text-[11px] text-slate-600 dark:text-gray-300">
                {reasons.length > 0 ? (
                  <ul className="list-disc space-y-0.5 pl-4">
                    {reasons.map((r, i) => <li key={i}>{r}</li>)}
                  </ul>
                ) : (
                  <p>Open the full analysis for the model&apos;s reasoning.</p>
                )}
                <button
                  onClick={() => setDetailOpen(true)}
                  className="rounded-lg border border-emerald-500/40 bg-emerald-500/[0.12] px-3 py-1 text-[11px] font-bold text-emerald-700 transition-colors hover:bg-emerald-500/20 dark:text-emerald-400"
                >
                  See more
                </button>
              </div>
            )}
          </div>
        </div>
      </GlassCard>

      {detailOpen && (
        <MatchDetailModal
          fixture={fixture}
          isSelected={!!isSelected}
          onSelectBet={onSelectBet}
          onClose={() => setDetailOpen(false)}
        />
      )}
    </>
  );
}
