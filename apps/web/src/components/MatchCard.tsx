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

function formatKickoff(f: Fixture): string {
  if (f.kickoff_timestamp) {
    const d = new Date(f.kickoff_timestamp);
    if (!Number.isNaN(d.getTime())) {
      return d.toLocaleString(undefined, { weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
    }
  }
  if (f.match_date && f.match_time) return `${f.match_date} · ${f.match_time}`;
  return f.kickoff;
}

/** Bento tile: teams, kick-off and win probabilities. Everything else lives behind "Why" and the detail modal. */
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

  const teamName = `min-w-0 truncate font-display font-semibold text-slate-900 dark:text-white ${featured ? "text-xl sm:text-2xl" : "text-base"}`;

  return (
    <>
      <GlassCard active={isSelected} className="flex h-full flex-col">
        <div className={`flex flex-1 flex-col gap-3 ${featured ? "p-5" : "p-4"}`}>
          <div className="flex items-center justify-between gap-2">
            <Chip tone="success" className="max-w-[55%] truncate uppercase tracking-wider">
              {fixture.league}
            </Chip>
            <div className="flex items-center gap-1.5">
              <span className="font-mono text-[11px] text-slate-500 dark:text-gray-400">{formatKickoff(fixture)}</span>
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
          </div>

          <div className="space-y-1.5">
            {[fixture.home_team, fixture.away_team].map((team, i) => (
              <div key={i} className="flex items-center gap-2.5">
                <Crest src={team.crest} name={team.name} size={featured ? 32 : 28} />
                <h3 className={teamName} title={team.name}>{team.name}</h3>
              </div>
            ))}
          </div>

          <div className="space-y-1">
            <div className="flex justify-between font-mono text-[11px] font-semibold">
              <span className="text-emerald-600 dark:text-emerald-400">1 <OddsText value={p.prob_home_win * 100} digits={0} suffix="%" /></span>
              <span className="text-slate-500 dark:text-gray-400">X <OddsText value={p.prob_draw * 100} digits={0} suffix="%" /></span>
              <span className="text-blue-600 dark:text-blue-400">2 <OddsText value={p.prob_away_win * 100} digits={0} suffix="%" /></span>
            </div>
            <div className="flex h-2 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-gray-800">
              <div style={{ width: `${p.prob_home_win * 100}%` }} className="bg-emerald-500" />
              <div style={{ width: `${p.prob_draw * 100}%` }} className="bg-slate-400 dark:bg-gray-600" />
              <div style={{ width: `${p.prob_away_win * 100}%` }} className="bg-blue-500" />
            </div>
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
