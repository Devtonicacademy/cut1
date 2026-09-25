"use client";

import React, { useState } from "react";
import { Fixture, ValueBetItem } from "@/types";
import { ChevronDown, ChevronUp, Sparkles, AlertTriangle, TrendingUp, CheckCircle2, Trophy, Shield } from "lucide-react";

interface MatchCardProps {
  fixture: Fixture;
  onSelectBet: (bet: ValueBetItem, fixture: Fixture) => void;
  isSelected?: boolean;
}

export default function MatchCard({ fixture, onSelectBet, isSelected }: MatchCardProps) {
  const [expanded, setExpanded] = useState(false);
  const p = fixture.prediction;

  if (!p) return null;

  const topValueBet = p.value_bets.length > 0 ? p.value_bets[0] : null;

  return (
    <div className={`rounded-xl border transition-all ${
      isSelected 
        ? "bg-[#11192e] border-emerald-500/80 shadow-lg glow-emerald"
        : "bg-[#0d1322] border-gray-800 hover:border-gray-700"
    }`}>
      {/* Top Banner: League & Kickoff */}
      <div className="px-4 py-2 bg-gray-900/60 border-b border-gray-800/80 flex justify-between items-center text-xs">
        <span className="font-semibold text-emerald-400 uppercase tracking-wider text-[11px]">
          {fixture.league}
        </span>
        <span className="text-gray-400 font-mono text-[11px]">
          {fixture.kickoff}
        </span>
      </div>

      {/* Main Matchup Body */}
      <div className="p-4">
        {/* Statistically Projected Winner Highlight */}
        {p.likely_winner_team && (
          <div className="mb-3 p-2.5 rounded-lg bg-gradient-to-r from-emerald-950/60 via-gray-900 to-[#101726] border border-emerald-500/30 flex items-center justify-between gap-2 text-xs">
            <div className="flex items-center gap-2">
              <span className="p-1.5 rounded-md bg-emerald-500/20 text-emerald-400">
                <Trophy className="w-3.5 h-3.5 fill-emerald-400/30" />
              </span>
              <div>
                <div className="flex items-center gap-1.5 flex-wrap">
                  <span className="text-[10px] text-gray-400 font-bold uppercase tracking-wider">Likely Winner:</span>
                  <span className="font-black text-white text-xs">{p.likely_winner_team}</span>
                  <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded border ${
                    p.likely_winner_confidence?.includes("Banker")
                      ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
                      : p.likely_winner_confidence?.includes("Strong")
                      ? "bg-amber-500/20 text-amber-300 border-amber-500/40"
                      : "bg-blue-500/20 text-blue-300 border-blue-500/40"
                  }`}>
                    {((p.likely_winner_prob || 0) * 100).toFixed(0)}% Win Prob • {p.likely_winner_confidence}
                  </span>
                </div>
                {p.recommended_safe_pick && (
                  <p className="text-[11px] text-emerald-400/90 mt-0.5 flex items-center gap-1">
                    <Shield className="w-3 h-3 inline text-emerald-400" />
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
            <h3 className="font-extrabold text-sm sm:text-base text-white">{fixture.home_team.name}</h3>
            <div className="flex justify-end gap-1 mt-1">
              {fixture.home_team.form.split("").map((f, i) => (
                <span
                  key={i}
                  className={`text-[9px] font-bold px-1 rounded ${
                    f === "W" ? "bg-emerald-600/80 text-white" : f === "D" ? "bg-gray-600 text-white" : "bg-red-700 text-white"
                  }`}
                >
                  {f}
                </span>
              ))}
            </div>
            <p className="text-[10px] text-gray-400 mt-0.5">xG: {fixture.home_team.rolling_xg_created.toFixed(2)}</p>
          </div>

          {/* VS Divider & Score Expectancy */}
          <div className="col-span-1 text-center">
            <span className="text-xs font-black text-gray-500 bg-gray-900 px-2 py-1 rounded-full border border-gray-800">
              VS
            </span>
            <p className="text-[10px] text-gray-400 mt-1 font-mono">
              xG: {p.expected_goals_home.toFixed(1)} - {p.expected_goals_away.toFixed(1)}
            </p>
          </div>

          {/* Away Team */}
          <div className="col-span-2 text-left">
            <h3 className="font-extrabold text-sm sm:text-base text-white">{fixture.away_team.name}</h3>
            <div className="flex justify-start gap-1 mt-1">
              {fixture.away_team.form.split("").map((f, i) => (
                <span
                  key={i}
                  className={`text-[9px] font-bold px-1 rounded ${
                    f === "W" ? "bg-emerald-600/80 text-white" : f === "D" ? "bg-gray-600 text-white" : "bg-red-700 text-white"
                  }`}
                >
                  {f}
                </span>
              ))}
            </div>
            <p className="text-[10px] text-gray-400 mt-0.5">xG: {fixture.away_team.rolling_xg_created.toFixed(2)}</p>
          </div>
        </div>

        {/* AI Calibrated Probability Bar */}
        <div className="space-y-1 mb-3">
          <div className="flex justify-between text-[11px] font-semibold">
            <span className="text-emerald-400">1: {(p.prob_home_win * 100).toFixed(0)}%</span>
            <span className="text-gray-400">X: {(p.prob_draw * 100).toFixed(0)}%</span>
            <span className="text-blue-400">2: {(p.prob_away_win * 100).toFixed(0)}%</span>
          </div>
          <div className="h-2 w-full bg-gray-800 rounded-full overflow-hidden flex">
            <div style={{ width: `${p.prob_home_win * 100}%` }} className="bg-emerald-500" />
            <div style={{ width: `${p.prob_draw * 100}%` }} className="bg-gray-600" />
            <div style={{ width: `${p.prob_away_win * 100}%` }} className="bg-blue-500" />
          </div>
        </div>

        {/* Best +EV Value Play Callout */}
        {topValueBet && (
          <div className="bg-emerald-950/40 border border-emerald-500/40 rounded-lg p-2.5 mb-3 flex flex-wrap justify-between items-center gap-2">
            <div className="flex items-center gap-2">
              <span className="bg-gold-500 text-black text-[10px] font-black px-1.5 py-0.5 rounded uppercase">
                +{topValueBet.expected_value_pct.toFixed(1)}% EV
              </span>
              <div>
                <span className="font-extrabold text-xs text-white">{topValueBet.market_name}</span>
                <span className="text-[11px] text-gray-400 ml-1.5">
                  best on <b className="text-emerald-300">{topValueBet.bookmaker}</b> ({topValueBet.market_odds.toFixed(2)})
                </span>
              </div>
            </div>

            <button
              onClick={() => onSelectBet(topValueBet, fixture)}
              className={`text-xs font-bold px-3 py-1 rounded-md transition-all flex items-center gap-1 ${
                isSelected
                  ? "bg-emerald-500 text-black shadow"
                  : "bg-emerald-700/60 hover:bg-emerald-600 text-white"
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
        <div className="grid grid-cols-2 gap-2 text-xs bg-gray-900/40 p-2 rounded-lg border border-gray-800/60">
          <div className="flex justify-between items-center">
            <span className="text-gray-400 font-medium">SportyBet:</span>
            <span className="font-mono text-white">
              1: <b className="text-emerald-400">{fixture.sportybet_odds.home_win.toFixed(2)}</b> | 
              X: <b>{fixture.sportybet_odds.draw.toFixed(2)}</b> | 
              2: <b>{fixture.sportybet_odds.away_win.toFixed(2)}</b>
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-gray-400 font-medium">Bet9ja:</span>
            <span className="font-mono text-white">
              1: <b className="text-emerald-400">{fixture.bet9ja_odds.home_win.toFixed(2)}</b> | 
              X: <b>{fixture.bet9ja_odds.draw.toFixed(2)}</b> | 
              2: <b>{fixture.bet9ja_odds.away_win.toFixed(2)}</b>
            </span>
          </div>
        </div>

        {/* Toggle Details Drawer */}
        <button
          onClick={() => setExpanded(!expanded)}
          className="w-full mt-3 pt-2 border-t border-gray-800 text-[11px] font-semibold text-gray-400 hover:text-white flex items-center justify-center gap-1"
        >
          <span>{expanded ? "Hide AI Breakdown" : "View Gemini Tactical Breakdown & Stats"}</span>
          {expanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </button>

        {/* Expanded Drawer: Gemini Analysis, Injuries & Alternative Value Plays */}
        {expanded && (
          <div className="mt-3 pt-3 border-t border-gray-800/80 space-y-2.5 text-xs text-gray-300">
            {/* Statistical Model Verdict */}
            {p.statistical_verdict && (
              <div className="bg-[#121f2d] p-3 rounded-lg border border-emerald-500/30">
                <div className="flex items-center gap-1.5 text-emerald-400 font-bold mb-1">
                  <Trophy className="w-3.5 h-3.5" />
                  <span>Dixon-Coles & xG Statistical Verdict</span>
                </div>
                <p className="text-gray-200 leading-relaxed text-[11px]">
                  {p.statistical_verdict}
                </p>
              </div>
            )}

            {/* Gemini Tactical Rationale */}
            <div className="bg-[#12192a] p-3 rounded-lg border border-gray-700/60">
              <div className="flex items-center gap-1.5 text-gold-400 font-bold mb-1">
                <Sparkles className="w-3.5 h-3.5" />
                <span>Google Gemini AI Match Analysis</span>
              </div>
              <p className="text-gray-200 leading-relaxed text-[11px] mb-2">
                {p.gemini_tactical_summary}
              </p>
              <div className="flex items-start gap-1.5 text-amber-300/90 text-[10px] bg-amber-950/40 p-1.5 rounded">
                <AlertTriangle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                <span>{p.gemini_lineup_risk}</span>
              </div>
            </div>

            {/* Other Value Plays in this Match */}
            {p.value_bets.length > 1 && (
              <div>
                <h4 className="font-bold text-[11px] text-gray-400 mb-1.5 uppercase tracking-wide">
                  Alternative Value Markets:
                </h4>
                <div className="space-y-1.5">
                  {p.value_bets.slice(1, 4).map((vb, idx) => (
                    <div
                      key={idx}
                      className="flex justify-between items-center bg-gray-900/60 px-2.5 py-1.5 rounded border border-gray-800"
                    >
                      <span className="font-medium text-white">{vb.market_name}</span>
                      <div className="flex items-center gap-2">
                        <span className="text-emerald-400 font-bold font-mono">
                          +{vb.expected_value_pct.toFixed(1)}% EV ({vb.market_odds.toFixed(2)})
                        </span>
                        <button
                          onClick={() => onSelectBet(vb, fixture)}
                          className="bg-gray-800 hover:bg-emerald-600 hover:text-black text-gray-200 text-[10px] font-bold px-2 py-0.5 rounded transition-colors"
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
