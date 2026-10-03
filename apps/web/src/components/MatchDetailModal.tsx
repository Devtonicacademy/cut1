"use client";

import React, { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import {
  AlertTriangle, BarChart2, Check, CheckCircle2, ExternalLink, Sparkles, Trophy, TrendingUp, X,
} from "lucide-react";
import { Fixture, ValueBetItem } from "@/types";
import OddsText from "@/components/ui/OddsText";

interface MatchDetailModalProps {
  fixture: Fixture;
  isSelected: boolean;
  onSelectBet: (bet: ValueBetItem, fixture: Fixture) => void;
  onClose: () => void;
}

const BOOKMAKERS = [
  { name: "SportyBet", url: "https://www.sportybet.com/ng/" },
  { name: "Bet9ja", url: "https://sports.bet9ja.com/" },
];

/**
 * Full match detail: head-to-head, model analysis, value bets and bookmaker links.
 * Rendered in a portal because the cards use backdrop-filter, which would otherwise trap a `fixed` child.
 */
export default function MatchDetailModal({ fixture, isSelected, onSelectBet, onClose }: MatchDetailModalProps) {
  const [mounted, setMounted] = useState(false);
  const [copiedBook, setCopiedBook] = useState<string | null>(null);
  const closeRef = useRef<HTMLButtonElement>(null);
  // Keep the latest onClose without re-running the focus/scroll-lock effect when the parent re-renders.
  const onCloseRef = useRef(onClose);
  onCloseRef.current = onClose;
  const p = fixture.prediction;
  const h2h = fixture.h2h;

  useEffect(() => setMounted(true), []);

  // Escape closes; the page behind stops scrolling; focus moves in and is restored on close.
  useEffect(() => {
    if (!mounted) return;
    const previouslyFocused = document.activeElement as HTMLElement | null;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onCloseRef.current();
    document.addEventListener("keydown", onKey);
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    closeRef.current?.focus();
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = prevOverflow;
      previouslyFocused?.focus();
    };
  }, [mounted]);

  if (!mounted || !p) return null;

  const topValueBet = p.value_bets[0] ?? null;
  const hasMarketOdds = fixture.sportybet_odds.bookmaker === "Market Average";

  const findOnBookmaker = (name: string, url: string) => {
    try {
      navigator.clipboard.writeText(`${fixture.home_team.name} vs ${fixture.away_team.name}`);
    } catch {
      // clipboard unavailable: the site still opens
    }
    setCopiedBook(name);
    setTimeout(() => setCopiedBook(null), 2500);
    window.open(url, "_blank", "noopener,noreferrer");
  };

  return createPortal(
    <div className="fixed inset-0 z-[60] flex items-end justify-center sm:items-center sm:p-6">
      {/* Blurred backdrop */}
      <div className="absolute inset-0 bg-black/50 backdrop-blur-md" onClick={onClose} aria-hidden="true" />

      <div
        role="dialog"
        aria-modal="true"
        aria-label={`${fixture.home_team.name} vs ${fixture.away_team.name}`}
        className="relative flex max-h-[90vh] w-full max-w-2xl flex-col overflow-hidden rounded-t-2xl border border-slate-200 bg-white shadow-modal dark:border-white/[0.12] dark:bg-surface-modal dark:backdrop-blur-modal sm:rounded-panel"
      >
        <div className="flex items-start justify-between gap-3 border-b border-slate-200 p-4 dark:border-white/[0.08]">
          <div className="min-w-0">
            <p className="font-mono text-[10px] font-semibold uppercase tracking-wider text-emerald-600 dark:text-emerald-400">{fixture.league}</p>
            <h2 className="truncate font-display text-lg font-semibold text-slate-900 dark:text-white">
              {fixture.home_team.name} <span className="text-slate-400">vs</span> {fixture.away_team.name}
            </h2>
          </div>
          <button
            ref={closeRef}
            onClick={onClose}
            aria-label="Close"
            className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100 dark:text-gray-400 dark:hover:bg-slate-800"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="space-y-4 overflow-y-auto p-4 text-xs text-slate-700 dark:text-gray-300">
          {/* Best +EV value play */}
          {topValueBet && (
            <div className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-emerald-500/30 bg-emerald-50/90 p-2.5 dark:bg-emerald-950/40">
              <div className="flex items-center gap-2">
                <span className="rounded bg-amber-400 px-1.5 py-0.5 text-[10px] font-black uppercase text-slate-900 dark:bg-gold-500 dark:text-black">
                  <OddsText value={topValueBet.expected_value_pct} digits={1} prefix="+" suffix="% EV" />
                </span>
                <span className="font-extrabold text-slate-900 dark:text-white">{topValueBet.market_name}</span>
                <span className="text-[11px] text-slate-600 dark:text-gray-400">
                  best on <b className="text-emerald-700 dark:text-emerald-300">{topValueBet.bookmaker}</b> (<OddsText value={topValueBet.market_odds} />)
                </span>
              </div>
              <button
                onClick={() => onSelectBet(topValueBet, fixture)}
                className={`flex items-center gap-1 rounded-md px-3 py-1 text-xs font-bold text-white transition-all ${
                  isSelected ? "bg-emerald-600 shadow" : "bg-emerald-700/80 hover:bg-emerald-600"
                }`}
              >
                {isSelected ? (
                  <>
                    <CheckCircle2 className="h-3.5 w-3.5" />
                    <span>Selected</span>
                  </>
                ) : (
                  <>
                    <TrendingUp className="h-3.5 w-3.5" />
                    <span>Stake ₦{topValueBet.recommended_stake_ngn.toLocaleString()}</span>
                  </>
                )}
              </button>
            </div>
          )}

          {/* Head-to-head */}
          <section className="space-y-2.5 rounded-lg border border-blue-200 bg-slate-50 p-3 dark:border-blue-900/50 dark:bg-slate-900/60">
            <div className="flex items-center justify-between border-b border-slate-200 pb-2 dark:border-gray-800">
              <span className="flex items-center gap-1.5 font-extrabold text-slate-900 dark:text-white">
                <BarChart2 className="h-3.5 w-3.5 text-blue-500" />
                Head-to-Head Record
              </span>
              <span className="rounded bg-blue-100 px-2 py-0.5 font-mono text-[10px] font-semibold text-blue-800 dark:bg-blue-950 dark:text-blue-300">
                {h2h?.total_meetings ?? 0} matches
              </span>
            </div>
            {h2h && h2h.total_meetings > 0 ? (
              <>
                <div>
                  <div className="mb-1 flex justify-between text-[11px] font-bold">
                    <span className="text-emerald-600 dark:text-emerald-400">{fixture.home_team.name}: {h2h.home_team_wins}W</span>
                    <span className="text-slate-500 dark:text-gray-400">Draws: {h2h.draws}</span>
                    <span className="text-blue-600 dark:text-blue-400">{fixture.away_team.name}: {h2h.away_team_wins}W</span>
                  </div>
                  <div className="flex h-2 w-full overflow-hidden rounded-full bg-slate-200 dark:bg-gray-800">
                    <div style={{ width: `${(h2h.home_team_wins / h2h.total_meetings) * 100}%` }} className="bg-emerald-500" />
                    <div style={{ width: `${(h2h.draws / h2h.total_meetings) * 100}%` }} className="bg-slate-400 dark:bg-gray-600" />
                    <div style={{ width: `${(h2h.away_team_wins / h2h.total_meetings) * 100}%` }} className="bg-blue-500" />
                  </div>
                </div>
                {h2h.last_matches?.length > 0 && (
                  <div className="space-y-1">
                    <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-gray-400">Previous encounters</p>
                    {h2h.last_matches.map((m, idx) => (
                      <div
                        key={idx}
                        className="flex items-center justify-between gap-2 rounded border border-slate-200 bg-white p-2 text-[11px] dark:border-gray-700/60 dark:bg-gray-800/60"
                      >
                        <span className="truncate text-slate-600 dark:text-gray-400">
                          <span className="font-semibold text-slate-800 dark:text-gray-200">{m.date}</span>
                          <span className="ml-1 text-[10px]">({m.competition})</span>
                        </span>
                        <span className="shrink-0 font-mono font-extrabold text-slate-900 dark:text-white">
                          {m.home_team} {m.home_score} - {m.away_score} {m.away_team}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
                {h2h.summary && (
                  <p className="rounded border border-slate-200/60 bg-white/60 p-2 text-[11px] italic dark:border-gray-800 dark:bg-gray-800/40">
                    &ldquo;{h2h.summary}&rdquo;
                  </p>
                )}
              </>
            ) : (
              <p className="text-slate-500 dark:text-gray-400">No previous meetings on record.</p>
            )}
          </section>

          {/* Model analysis */}
          {p.statistical_verdict && (
            <section className="rounded-lg border border-emerald-500/30 bg-emerald-50/80 p-3 dark:bg-slate-800">
              <div className="mb-1 flex items-center gap-1.5 font-bold text-emerald-700 dark:text-emerald-400">
                <Trophy className="h-3.5 w-3.5" />
                Model verdict
              </div>
              <p className="text-[11px] leading-relaxed text-slate-800 dark:text-gray-200">{p.statistical_verdict}</p>
            </section>
          )}

          {(p.gemini_tactical_summary || p.gemini_lineup_risk) && (
            <section className="rounded-lg border border-slate-200 bg-slate-50 p-3 dark:border-gray-700/60 dark:bg-slate-800">
              <div className="mb-1 flex items-center gap-1.5 font-bold text-amber-600 dark:text-gold-400">
                <Sparkles className="h-3.5 w-3.5" />
                Match analysis
              </div>
              {p.gemini_tactical_summary && (
                <p className="mb-2 text-[11px] leading-relaxed text-slate-800 dark:text-gray-200">{p.gemini_tactical_summary}</p>
              )}
              {p.gemini_lineup_risk && (
                <div className="flex items-start gap-1.5 rounded border border-amber-200 bg-amber-50 p-2 text-[10px] text-amber-800 dark:border-amber-900/40 dark:bg-amber-950/40 dark:text-amber-300/90">
                  <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-amber-600" />
                  <span>{p.gemini_lineup_risk}</span>
                </div>
              )}
            </section>
          )}

          {/* Other value markets */}
          {p.value_bets.length > 1 && (
            <section>
              <h3 className="mb-1.5 text-[11px] font-bold uppercase tracking-wide text-slate-500 dark:text-gray-400">Other value markets</h3>
              <div className="space-y-1.5">
                {p.value_bets.slice(1, 4).map((vb, idx) => (
                  <div key={idx} className="flex items-center justify-between rounded border border-slate-200 bg-white px-2.5 py-1.5 dark:border-gray-800 dark:bg-gray-900/60">
                    <span className="font-medium text-slate-900 dark:text-white">{vb.market_name}</span>
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold text-emerald-600 dark:text-emerald-400">
                        <OddsText value={vb.expected_value_pct} digits={1} prefix="+" suffix="% EV" /> (<OddsText value={vb.market_odds} />)
                      </span>
                      <button
                        onClick={() => onSelectBet(vb, fixture)}
                        className="rounded bg-slate-100 px-2 py-0.5 text-[10px] font-bold text-slate-800 transition-colors hover:bg-emerald-600 hover:text-white dark:bg-gray-800 dark:text-gray-200 dark:hover:bg-emerald-600 dark:hover:text-black"
                      >
                        Select
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Bookmaker odds + links */}
          <section className="space-y-1 rounded-lg border border-slate-200/80 bg-slate-50 p-2 dark:border-gray-800/60 dark:bg-gray-900/40">
            {hasMarketOdds ? (
              [fixture.sportybet_odds, fixture.bet9ja_odds].map((book) => (
                <div key={book.bookmaker} className="flex items-center justify-between">
                  <span className="font-medium text-slate-500 dark:text-gray-400">{book.bookmaker}:</span>
                  <span className="font-mono text-slate-900 dark:text-white">
                    1: <b className="text-emerald-600 dark:text-emerald-400"><OddsText value={book.home_win} /></b> | X: <b><OddsText value={book.draw} /></b> | 2: <b><OddsText value={book.away_win} /></b>
                  </span>
                </div>
              ))
            ) : (
              <p className="text-slate-500 dark:text-gray-400">No bookmaker odds published yet for this match.</p>
            )}
            <div className="flex items-center gap-1.5 border-t border-slate-200 pt-1 dark:border-gray-800/60">
              <span className="mr-auto text-[10px] text-slate-500 dark:text-gray-400">
                {copiedBook ? `Match name copied: paste it into ${copiedBook} search` : "Check live odds:"}
              </span>
              {BOOKMAKERS.map((b) => (
                <button
                  key={b.name}
                  onClick={() => findOnBookmaker(b.name, b.url)}
                  className="inline-flex items-center gap-1 rounded border border-slate-300 px-2 py-0.5 text-[10px] font-bold text-slate-700 hover:bg-slate-100 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-800"
                >
                  {copiedBook === b.name ? <Check className="h-3 w-3" /> : <ExternalLink className="h-3 w-3" />}
                  {b.name}
                </button>
              ))}
            </div>
          </section>
        </div>
      </div>
    </div>,
    document.body,
  );
}
