"use client";

import React, { useState } from "react";
import { Fixture, ValueBetItem } from "@/types";
import { 
  ChevronDown, ChevronUp, Sparkles, AlertTriangle, TrendingUp, 
  CheckCircle2, Trophy, Shield, Calendar, Clock, BarChart2 
} from "lucide-react";

interface MatchCardProps {
  fixture: Fixture;
  onSelectBet: (bet: ValueBetItem, fixture: Fixture) => void;
  isSelected?: boolean;
}

export default function MatchCard({ fixture, onSelectBet, isSelected }: MatchCardProps) {
  const [expanded, setExpanded] = useState(false);
  const [showH2H, setShowH2H] = useState(false);
  const p = fixture.prediction;

  if (!p) return null;

  const topValueBet = p.value_bets.length > 0 ? p.value_bets[0] : null;

  // Format kick-off date & time
  const displayDate = fixture.match_date || (fixture.kickoff.includes(",") ? fixture.kickoff.split(",")[0].trim() : "Upcoming");
  const displayTime = fixture.match_time || (fixture.kickoff.includes(",") ? fixture.kickoff.split(",")[1].trim() + " WAT" : fixture.kickoff);

  const h2h = fixture.h2h;

  return (
    <div className={`rounded-xl border transition-all duration-200 overflow-hidden ${
      isSelected 
        ? "bg-emerald-50/70 dark:bg-[#11192e] border-emerald-500 shadow-md ring-1 ring-emerald-500/30"
        : "bg-white dark:bg-[#0d1322] border-slate-200 dark:border-gray-800 shadow-sm hover:border-slate-300 dark:hover:border-gray-700"
    }`}>
      {/* Top Banner: League & Kickoff Date/Time */}
      <div className="px-3.5 py-2.5 bg-slate-50 dark:bg-gray-900/70 border-b border-slate-200/80 dark:border-gray-800 flex flex-wrap justify-between items-center gap-2 text-xs">
        <div className="flex items-center gap-2">
          <span className="font-bold text-emerald-600 dark:text-emerald-400 uppercase tracking-wider text-[11px] bg-emerald-50 dark:bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-500/20">
            {fixture.league}
          </span>
          <span className="text-[11px] text-slate-500 dark:text-gray-400 hidden xs:inline">
            • {fixture.venue.split(",")[0]}
          </span>
        </div>

        {/* Date and Time Badge */}
        <div className="flex items-center gap-2 text-[11px] font-medium text-slate-600 dark:text-gray-300 bg-white dark:bg-gray-800/80 px-2.5 py-1 rounded-md border border-slate-200 dark:border-gray-700 shadow-2xs">
          <span className="flex items-center gap-1 font-semibold text-slate-700 dark:text-gray-200">
            <Calendar className="w-3.5 h-3.5 text-emerald-500" />
            <span>{displayDate}</span>
          </span>
          <span className="text-slate-300 dark:text-gray-600">|</span>
          <span className="flex items-center gap-1 text-slate-500 dark:text-gray-400">
            <Clock className="w-3 h-3 text-slate-400" />
            <span>{displayTime}</span>
          </span>
        </div>
      </div>

      {/* Main Matchup Body */}
      <div className="p-3.5 sm:p-4">
        {/* Statistically Projected Winner Highlight */}
        {p.likely_winner_team && (
          <div className="mb-3 p-2.5 rounded-lg bg-gradient-to-r from-emerald-50 via-slate-50 to-slate-100 dark:from-emerald-950/50 dark:via-gray-900 dark:to-[#101726] border border-emerald-500/20 dark:border-emerald-500/30 flex items-center justify-between gap-2 text-xs">
            <div className="flex items-center gap-2">
              <span className="p-1.5 rounded-md bg-emerald-500/20 text-emerald-600 dark:text-emerald-400">
                <Trophy className="w-3.5 h-3.5" />
              </span>
              <div>
                <div className="flex items-center gap-1.5 flex-wrap">
                  <span className="text-[10px] text-slate-500 dark:text-gray-400 font-bold uppercase tracking-wider">Likely Winner:</span>
                  <span className="font-extrabold text-slate-900 dark:text-white text-xs">{p.likely_winner_team}</span>
                  <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded border ${
                    p.likely_winner_confidence?.includes("Banker")
                      ? "bg-emerald-100 text-emerald-800 border-emerald-300 dark:bg-emerald-500/20 dark:text-emerald-300 dark:border-emerald-500/40"
                      : p.likely_winner_confidence?.includes("Strong")
                      ? "bg-amber-100 text-amber-800 border-amber-300 dark:bg-amber-500/20 dark:text-amber-300 dark:border-amber-500/40"
                      : "bg-blue-100 text-blue-800 border-blue-300 dark:bg-blue-500/20 dark:text-blue-300 dark:border-blue-500/40"
                  }`}>
                    {((p.likely_winner_prob || 0) * 100).toFixed(0)}% Win Prob • {p.likely_winner_confidence}
                  </span>
                </div>
                {p.recommended_safe_pick && (
                  <p className="text-[11px] text-emerald-700 dark:text-emerald-400 mt-0.5 flex items-center gap-1">
                    <Shield className="w-3 h-3 inline text-emerald-500" />
                    <span>Safe Anchor: <b>{p.recommended_safe_pick}</b> ({p.recommended_safe_odds?.toFixed(2)})</span>
                  </p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Teams and Form */}
        <div className="grid grid-cols-5 items-center gap-2 mb-3">
          {/* Home Team */}
          <div className="col-span-2 text-right">
            <h3 className="font-extrabold text-sm sm:text-base text-slate-900 dark:text-white truncate" title={fixture.home_team.name}>
              {fixture.home_team.name}
            </h3>
            <div className="flex justify-end gap-1 mt-1">
              {fixture.home_team.form.split("").map((f, i) => (
                <span
                  key={i}
                  className={`text-[9px] font-bold px-1 rounded ${
                    f === "W" 
                      ? "bg-emerald-600 text-white" 
                      : f === "D" 
                      ? "bg-slate-400 dark:bg-gray-600 text-white" 
                      : "bg-rose-600 text-white"
                  }`}
                >
                  {f}
                </span>
              ))}
            </div>
            <p className="text-[10px] text-slate-500 dark:text-gray-400 mt-0.5">xG: {fixture.home_team.rolling_xg_created.toFixed(2)}</p>
          </div>

          {/* VS Divider & Score Expectancy */}
          <div className="col-span-1 text-center">
            <span className="text-[11px] font-black text-slate-500 dark:text-gray-400 bg-slate-100 dark:bg-gray-900 px-2 py-0.5 rounded-full border border-slate-200 dark:border-gray-800">
              VS
            </span>
            <p className="text-[10px] text-slate-500 dark:text-gray-400 mt-1 font-mono">
              xG: {p.expected_goals_home.toFixed(1)} - {p.expected_goals_away.toFixed(1)}
            </p>
          </div>

          {/* Away Team */}
          <div className="col-span-2 text-left">
            <h3 className="font-extrabold text-sm sm:text-base text-slate-900 dark:text-white truncate" title={fixture.away_team.name}>
              {fixture.away_team.name}
            </h3>
            <div className="flex justify-start gap-1 mt-1">
              {fixture.away_team.form.split("").map((f, i) => (
                <span
                  key={i}
                  className={`text-[9px] font-bold px-1 rounded ${
                    f === "W" 
                      ? "bg-emerald-600 text-white" 
                      : f === "D" 
                      ? "bg-slate-400 dark:bg-gray-600 text-white" 
                      : "bg-rose-600 text-white"
                  }`}
                >
                  {f}
                </span>
              ))}
            </div>
            <p className="text-[10px] text-slate-500 dark:text-gray-400 mt-0.5">xG: {fixture.away_team.rolling_xg_created.toFixed(2)}</p>
          </div>
        </div>

        {/* AI Calibrated Probability Bar */}
        <div className="space-y-1 mb-3">
          <div className="flex justify-between text-[11px] font-semibold">
            <span className="text-emerald-600 dark:text-emerald-400 font-bold">1: {(p.prob_home_win * 100).toFixed(0)}%</span>
            <span className="text-slate-500 dark:text-gray-400">X: {(p.prob_draw * 100).toFixed(0)}%</span>
            <span className="text-blue-600 dark:text-blue-400 font-bold">2: {(p.prob_away_win * 100).toFixed(0)}%</span>
          </div>
          <div className="h-2 w-full bg-slate-100 dark:bg-gray-800 rounded-full overflow-hidden flex border border-slate-200 dark:border-transparent">
            <div style={{ width: `${p.prob_home_win * 100}%` }} className="bg-emerald-500" />
            <div style={{ width: `${p.prob_draw * 100}%` }} className="bg-slate-400 dark:bg-gray-600" />
            <div style={{ width: `${p.prob_away_win * 100}%` }} className="bg-blue-500" />
          </div>
        </div>

        {/* Best +EV Value Play Callout */}
        {topValueBet && (
          <div className="bg-emerald-50/90 dark:bg-emerald-950/40 border border-emerald-500/30 dark:border-emerald-500/40 rounded-lg p-2.5 mb-3 flex flex-wrap justify-between items-center gap-2">
            <div className="flex items-center gap-2">
              <span className="bg-amber-400 dark:bg-gold-500 text-slate-900 dark:text-black text-[10px] font-black px-1.5 py-0.5 rounded uppercase">
                +{topValueBet.expected_value_pct.toFixed(1)}% EV
              </span>
              <div>
                <span className="font-extrabold text-xs text-slate-900 dark:text-white">{topValueBet.market_name}</span>
                <span className="text-[11px] text-slate-600 dark:text-gray-400 ml-1.5">
                  best on <b className="text-emerald-700 dark:text-emerald-300">{topValueBet.bookmaker}</b> ({topValueBet.market_odds.toFixed(2)})
                </span>
              </div>
            </div>

            <button
              onClick={() => onSelectBet(topValueBet, fixture)}
              className={`text-xs font-bold px-3 py-1 rounded-md transition-all flex items-center gap-1 ${
                isSelected
                  ? "bg-emerald-600 text-white shadow"
                  : "bg-emerald-700/80 hover:bg-emerald-600 text-white"
              }`}
            >
              {isSelected ? (
                <>
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Selected</span>
                </>
              ) : (
                <>
                  <TrendingUp className="w-3.5 h-3.5" />
                  <span>Stake ₦{topValueBet.recommended_stake_ngn.toLocaleString()}</span>
                </>
              )}
            </button>
          </div>
        )}

        {/* Odds Comparison Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs bg-slate-50 dark:bg-gray-900/40 p-2 rounded-lg border border-slate-200/80 dark:border-gray-800/60 mb-2.5">
          <div className="flex justify-between items-center">
            <span className="text-slate-500 dark:text-gray-400 font-medium">SportyBet:</span>
            <span className="font-mono text-slate-900 dark:text-white">
              1: <b className="text-emerald-600 dark:text-emerald-400">{fixture.sportybet_odds.home_win.toFixed(2)}</b> | 
              X: <b>{fixture.sportybet_odds.draw.toFixed(2)}</b> | 
              2: <b>{fixture.sportybet_odds.away_win.toFixed(2)}</b>
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-slate-500 dark:text-gray-400 font-medium">Bet9ja:</span>
            <span className="font-mono text-slate-900 dark:text-white">
              1: <b className="text-emerald-600 dark:text-emerald-400">{fixture.bet9ja_odds.home_win.toFixed(2)}</b> | 
              X: <b>{fixture.bet9ja_odds.draw.toFixed(2)}</b> | 
              2: <b>{fixture.bet9ja_odds.away_win.toFixed(2)}</b>
            </span>
          </div>
        </div>

        {/* Action Buttons: Head-to-Head & AI Breakdown */}
        <div className="grid grid-cols-2 gap-2 mt-2 pt-2 border-t border-slate-200 dark:border-gray-800">
          <button
            onClick={() => setShowH2H(!showH2H)}
            className={`py-1.5 px-2 rounded-md text-[11px] font-bold flex items-center justify-center gap-1.5 transition-colors border ${
              showH2H 
                ? "bg-blue-50 dark:bg-blue-950/40 border-blue-400 text-blue-600 dark:text-blue-300"
                : "bg-slate-100 hover:bg-slate-200 dark:bg-gray-800/80 dark:hover:bg-gray-700 border-slate-200 dark:border-gray-700 text-slate-700 dark:text-gray-300"
            }`}
          >
            <BarChart2 className="w-3.5 h-3.5" />
            <span>{showH2H ? "Hide H2H" : `H2H Stats (${h2h?.total_meetings || 5}+)`}</span>
          </button>

          <button
            onClick={() => setExpanded(!expanded)}
            className={`py-1.5 px-2 rounded-md text-[11px] font-bold flex items-center justify-center gap-1.5 transition-colors border ${
              expanded
                ? "bg-emerald-50 dark:bg-emerald-950/40 border-emerald-400 text-emerald-700 dark:text-emerald-300"
                : "bg-slate-100 hover:bg-slate-200 dark:bg-gray-800/80 dark:hover:bg-gray-700 border-slate-200 dark:border-gray-700 text-slate-700 dark:text-gray-300"
            }`}
          >
            <Sparkles className="w-3.5 h-3.5 text-amber-500" />
            <span>{expanded ? "Hide AI" : "AI Tactical"}</span>
            {expanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
          </button>
        </div>

        {/* Head-to-Head Statistics Drawer */}
        {showH2H && h2h && (
          <div className="mt-3 p-3 rounded-lg bg-slate-50 dark:bg-gray-900/80 border border-blue-200 dark:border-blue-900/50 space-y-2.5 text-xs animate-in fade-in duration-150">
            <div className="flex justify-between items-center border-b border-slate-200 dark:border-gray-800 pb-2">
              <span className="font-extrabold text-slate-900 dark:text-white flex items-center gap-1.5 text-xs">
                <BarChart2 className="w-3.5 h-3.5 text-blue-500" />
                <span>Head-to-Head Record</span>
              </span>
              <span className="text-[10px] bg-blue-100 dark:bg-blue-950 text-blue-800 dark:text-blue-300 px-2 py-0.5 rounded font-bold">
                {h2h.total_meetings} Total Matches
              </span>
            </div>

            {/* Wins Breakdown Bar */}
            <div>
              <div className="flex justify-between text-[11px] font-bold mb-1">
                <span className="text-emerald-600 dark:text-emerald-400">{fixture.home_team.name}: {h2h.home_team_wins}W</span>
                <span className="text-slate-500 dark:text-gray-400">Draws: {h2h.draws}</span>
                <span className="text-blue-600 dark:text-blue-400">{fixture.away_team.name}: {h2h.away_team_wins}W</span>
              </div>
              <div className="h-2 w-full bg-slate-200 dark:bg-gray-800 rounded-full overflow-hidden flex">
                <div style={{ width: `${(h2h.home_team_wins / (h2h.total_meetings || 1)) * 100}%` }} className="bg-emerald-500" title={`${fixture.home_team.name} wins`} />
                <div style={{ width: `${(h2h.draws / (h2h.total_meetings || 1)) * 100}%` }} className="bg-slate-400 dark:bg-gray-600" title="Draws" />
                <div style={{ width: `${(h2h.away_team_wins / (h2h.total_meetings || 1)) * 100}%` }} className="bg-blue-500" title={`${fixture.away_team.name} wins`} />
              </div>
            </div>

            {/* Past Meetings List */}
            {h2h.last_matches && h2h.last_matches.length > 0 && (
              <div className="space-y-1.5 pt-1">
                <p className="text-[10px] uppercase font-bold text-slate-500 dark:text-gray-400 tracking-wider">
                  Previous Encounters
                </p>
                <div className="space-y-1">
                  {h2h.last_matches.map((m, idx) => (
                    <div 
                      key={idx}
                      className="flex items-center justify-between p-2 rounded bg-white dark:bg-gray-800/60 border border-slate-200 dark:border-gray-700/60 text-[11px]"
                    >
                      <div className="text-slate-600 dark:text-gray-400 truncate max-w-[130px] sm:max-w-none">
                        <span className="font-semibold text-slate-800 dark:text-gray-200">{m.date}</span>
                        <span className="text-[10px] text-slate-400 dark:text-gray-500 ml-1 hidden xs:inline">({m.competition})</span>
                      </div>

                      <div className="flex items-center gap-2">
                        <span className="font-extrabold text-slate-900 dark:text-white font-mono">
                          {m.home_team} {m.home_score} - {m.away_score} {m.away_team}
                        </span>
                        <span className={`text-[9px] font-black px-1.5 py-0.5 rounded uppercase ${
                          m.winner === "home" 
                            ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300"
                            : m.winner === "draw"
                            ? "bg-slate-200 text-slate-700 dark:bg-gray-700 dark:text-gray-300"
                            : "bg-blue-100 text-blue-800 dark:bg-blue-950/60 dark:text-blue-300"
                        }`}>
                          {m.winner === "draw" ? "D" : `${m.winner === "home" ? m.home_team.slice(0,3) : m.away_team.slice(0,3)} Win`}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Narrative summary */}
            {h2h.summary && (
              <p className="text-[11px] text-slate-600 dark:text-gray-300 italic bg-white/60 dark:bg-gray-800/40 p-2 rounded border border-slate-200/60 dark:border-gray-800">
                &ldquo;{h2h.summary}&rdquo;
              </p>
            )}
          </div>
        )}

        {/* Expanded Drawer: Gemini Analysis, Injuries & Alternative Value Plays */}
        {expanded && (
          <div className="mt-3 pt-3 border-t border-slate-200 dark:border-gray-800/80 space-y-2.5 text-xs text-slate-700 dark:text-gray-300 animate-in fade-in duration-150">
            {/* Statistical Model Verdict */}
            {p.statistical_verdict && (
              <div className="bg-emerald-50/80 dark:bg-[#121f2d] p-3 rounded-lg border border-emerald-500/20 dark:border-emerald-500/30">
                <div className="flex items-center gap-1.5 text-emerald-700 dark:text-emerald-400 font-bold mb-1">
                  <Trophy className="w-3.5 h-3.5" />
                  <span>Dixon-Coles & xG Statistical Verdict</span>
                </div>
                <p className="text-slate-800 dark:text-gray-200 leading-relaxed text-[11px]">
                  {p.statistical_verdict}
                </p>
              </div>
            )}

            {/* Gemini Tactical Rationale */}
            <div className="bg-slate-50 dark:bg-[#12192a] p-3 rounded-lg border border-slate-200 dark:border-gray-700/60">
              <div className="flex items-center gap-1.5 text-amber-600 dark:text-gold-400 font-bold mb-1">
                <Sparkles className="w-3.5 h-3.5" />
                <span>Google Gemini AI Match Analysis</span>
              </div>
              <p className="text-slate-800 dark:text-gray-200 leading-relaxed text-[11px] mb-2">
                {p.gemini_tactical_summary}
              </p>
              <div className="flex items-start gap-1.5 text-amber-800 dark:text-amber-300/90 text-[10px] bg-amber-50 dark:bg-amber-950/40 p-2 rounded border border-amber-200 dark:border-amber-900/40">
                <AlertTriangle className="w-3.5 h-3.5 shrink-0 mt-0.5 text-amber-600" />
                <span>{p.gemini_lineup_risk}</span>
              </div>
            </div>

            {/* Other Value Plays in this Match */}
            {p.value_bets.length > 1 && (
              <div>
                <h4 className="font-bold text-[11px] text-slate-500 dark:text-gray-400 mb-1.5 uppercase tracking-wide">
                  Alternative Value Markets:
                </h4>
                <div className="space-y-1.5">
                  {p.value_bets.slice(1, 4).map((vb, idx) => (
                    <div
                      key={idx}
                      className="flex justify-between items-center bg-white dark:bg-gray-900/60 px-2.5 py-1.5 rounded border border-slate-200 dark:border-gray-800"
                    >
                      <span className="font-medium text-slate-900 dark:text-white">{vb.market_name}</span>
                      <div className="flex items-center gap-2">
                        <span className="text-emerald-600 dark:text-emerald-400 font-bold font-mono">
                          +{vb.expected_value_pct.toFixed(1)}% EV ({vb.market_odds.toFixed(2)})
                        </span>
                        <button
                          onClick={() => onSelectBet(vb, fixture)}
                          className="bg-slate-100 hover:bg-emerald-600 hover:text-white dark:bg-gray-800 dark:hover:bg-emerald-600 dark:hover:text-black text-slate-800 dark:text-gray-200 text-[10px] font-bold px-2 py-0.5 rounded transition-colors"
                        >
                          Select
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
