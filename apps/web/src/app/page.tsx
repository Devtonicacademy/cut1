"use client";

import React, { useState, useEffect } from "react";
import Header from "@/components/Header";
import MatchCard from "@/components/MatchCard";
import KellyCalculator from "@/components/KellyCalculator";
import SmartAccaModal from "@/components/SmartAccaModal";
import WhatsAppSlipGenerator from "@/components/WhatsAppSlipGenerator";
import TrackRecordView from "@/components/TrackRecordView";
import AccuracyView from "@/components/AccuracyView";
import MobileBottomNav from "@/components/MobileBottomNav";
import AgeGate from "@/components/AgeGate";
import { API_BASE_URL } from "@/lib/config";
import {
  Fixture, ValueBetItem, AccumulatorResponse, TrackRecordStats, ModelReport, ChainVerification,
} from "@/types";
import { Zap, ShieldCheck, Sparkles, RefreshCw, Layers, BarChart2 } from "lucide-react";

async function getJson<T>(path: string, init?: RequestInit): Promise<T | null> {
  try {
    const res = await fetch(`${API_BASE_URL}${path}`, init);
    return res.ok ? ((await res.json()) as T) : null;
  } catch {
    return null;
  }
}

export default function Home() {
  const [bankroll, setBankroll] = useState<number>(10000);
  const [dataSaver, setDataSaver] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<string>("fixtures");
  const [fixtures, setFixtures] = useState<Fixture[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [loadError, setLoadError] = useState<boolean>(false);
  const [selectedBets, setSelectedBets] = useState<ValueBetItem[]>([]);
  const [selectedLeague, setSelectedLeague] = useState<string>("All");
  const [selectedConfidence, setSelectedConfidence] = useState<string>("All");
  const [accaLoading, setAccaLoading] = useState<boolean>(false);
  const [isDarkMode, setIsDarkMode] = useState<boolean>(true);

  const [bankerData, setBankerData] = useState<AccumulatorResponse | null>(null);
  const [showBankerModal, setShowBankerModal] = useState<boolean>(false);
  const [showShareModal, setShowShareModal] = useState<boolean>(false);
  const [trackStats, setTrackStats] = useState<TrackRecordStats | null>(null);
  const [verification, setVerification] = useState<ChainVerification | null>(null);
  const [modelReport, setModelReport] = useState<ModelReport | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  useEffect(() => {
    let isDark = true;
    try {
      const savedTheme = localStorage.getItem("livelyborg_theme");
      if (savedTheme) isDark = savedTheme === "dark";
    } catch {
      // storage blocked: keep the default theme
    }
    setIsDarkMode(isDark);
    document.documentElement.classList.toggle("dark", isDark);
  }, []);

  const toggleTheme = () => {
    setIsDarkMode((prev) => {
      const next = !prev;
      document.documentElement.classList.toggle("dark", next);
      try {
        localStorage.setItem("livelyborg_theme", next ? "dark" : "light");
      } catch {
        // storage blocked
      }
      return next;
    });
  };

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3500);
  };

  const toggleDataSaver = () => {
    setDataSaver((prev) => {
      const next = !prev;
      document.body.classList.toggle("data-saver", next);
      showToast(next ? "Data Saver on: fewer animations and graphics." : "Data Saver off.");
      return next;
    });
  };

  const fetchFixtures = async () => {
    setLoading(true);
    const data = await getJson<Fixture[]>(`/fixtures?bankroll=${bankroll}`);
    setLoadError(data === null);
    if (data) setFixtures(data);
    setLoading(false);
  };

  const fetchTrackRecord = async () => {
    const [stats, verify] = await Promise.all([
      getJson<TrackRecordStats>("/track-record"),
      getJson<ChainVerification>("/track-record/verify"),
    ]);
    setTrackStats(stats);
    setVerification(verify);
  };

  useEffect(() => {
    fetchFixtures();
    fetchTrackRecord();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [bankroll]);

  useEffect(() => {
    getJson<ModelReport>("/model/report").then(setModelReport);
  }, []);

  const openSlip = async (body: Record<string, unknown>) => {
    setAccaLoading(true);
    const data = await getJson<AccumulatorResponse>("/accumulators/build", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ bankroll_ngn: bankroll, ...body }),
    });
    setAccaLoading(false);
    if (!data) {
      showToast("Couldn't build a slip right now. Please try again.");
      return;
    }
    setBankerData(data);
    setShowBankerModal(true);
  };

  const buildMultiGameAcca = (targetLegs: number = 5, strategy: string = "safest") =>
    openSlip({ target_legs: targetLegs, strategy });

  // A short slip of straight wins reaching about 2.0 total odds
  const loadDailyBanker = () => openSlip({ target_odds: 2.0, max_legs: 4, strategy: "straight_win" });

  const handleSelectBet = (bet: ValueBetItem) => {
    setSelectedBets((prev) => {
      if (prev.some((b) => b.market_name === bet.market_name)) {
        showToast(`Removed "${bet.market_name}".`);
        return prev.filter((b) => b.market_name !== bet.market_name);
      }
      showToast(`Added "${bet.market_name}" (${bet.market_odds.toFixed(2)}) to the stake calculator.`);
      return [...prev, bet];
    });
  };

  const handleRemoveBet = (index: number) => {
    setSelectedBets((prev) => prev.filter((_, i) => i !== index));
  };

  // Value bets only exist when they passed the backtest; otherwise the stake calculator is hidden
  const showKelly = selectedBets.length > 0 || fixtures.some((f) => (f.prediction?.value_bets.length ?? 0) > 0);

  const leagueCounts = fixtures.reduce<Record<string, number>>((acc, f) => {
    acc[f.league] = (acc[f.league] || 0) + 1;
    return acc;
  }, {});
  const leagues = ["All", ...Object.keys(leagueCounts).sort((a, b) => leagueCounts[b] - leagueCounts[a])];

  const filteredFixtures = fixtures.filter((f) => {
    if (selectedLeague !== "All" && f.league !== selectedLeague) return false;
    const prob = f.prediction?.likely_winner_prob || 0;
    if (selectedConfidence === "Bankers") return prob >= 0.7;
    if (selectedConfidence === "Favorites") return prob >= 0.58;
    return true;
  });

  return (
    <AgeGate>
      <div className="min-h-screen bg-slate-50 text-slate-900 dark:bg-[#090d16] dark:text-gray-100 flex flex-col transition-colors duration-150 pb-20 md:pb-0">
        {toastMessage && (
          <div className="fixed bottom-20 md:bottom-4 right-4 z-50 bg-emerald-600 dark:bg-emerald-500 text-white dark:text-black font-extrabold text-xs px-4 py-2.5 rounded-xl shadow-2xl flex items-center gap-2 animate-in fade-in slide-in-from-bottom-2">
            <Sparkles className="w-4 h-4 fill-current" />
            <span>{toastMessage}</span>
          </div>
        )}

        <Header
          bankroll={bankroll}
          onBankrollChange={setBankroll}
          dataSaver={dataSaver}
          onToggleDataSaver={toggleDataSaver}
          activeTab={activeTab}
          onSelectTab={setActiveTab}
          onOpenBankerModal={loadDailyBanker}
          onOpenAccaBuilder={(count) => buildMultiGameAcca(count)}
          showKelly={showKelly}
          isDarkMode={isDarkMode}
          onToggleTheme={toggleTheme}
        />

        <main className="flex-1 max-w-6xl w-full mx-auto px-3.5 sm:px-6 py-4 sm:py-6">
          {activeTab === "fixtures" && (
            <div className="space-y-4 sm:space-y-6">
              {/* Hero */}
              <div className="bg-white dark:bg-gradient-to-r dark:from-[#121c33] dark:via-[#0d1424] dark:to-[#0a0f1d] border border-slate-200 dark:border-emerald-500/30 rounded-2xl p-4 sm:p-6 shadow-sm">
                <div className="max-w-3xl">
                  <div className="inline-flex items-center gap-1.5 bg-emerald-50 text-emerald-800 dark:bg-emerald-500/20 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-500/30 text-[11px] sm:text-xs font-bold px-3 py-1 rounded-full mb-2.5">
                    <ShieldCheck className="w-3.5 h-3.5" />
                    <span>Trained on 70,000+ real matches • every pick locked before kickoff</span>
                  </div>
                  <h2 className="text-lg sm:text-2xl font-black text-slate-900 dark:text-white tracking-tight">
                    Honest football predictions, <span className="text-emerald-600 dark:text-emerald-400">not guesses</span>.
                  </h2>
                  <p className="text-xs sm:text-sm text-slate-600 dark:text-gray-300 mt-1 leading-relaxed">
                    Win, draw and loss chances from a model tested against the bookmakers, the reasons behind every pick,
                    and a public track record anyone can verify.
                  </p>

                  <div className="mt-3.5 flex flex-wrap items-center gap-2">
                    <button
                      onClick={loadDailyBanker}
                      disabled={accaLoading}
                      className="bg-emerald-600 hover:bg-emerald-700 dark:bg-emerald-500 dark:hover:bg-emerald-400 text-white dark:text-black font-black text-xs px-3.5 py-2 rounded-xl flex items-center gap-1.5"
                    >
                      <Zap className="w-3.5 h-3.5 fill-current" />
                      <span>2-Odds Slip</span>
                    </button>
                    {[5, 10].map((n) => (
                      <button
                        key={n}
                        onClick={() => buildMultiGameAcca(n)}
                        disabled={accaLoading}
                        className="bg-white hover:bg-slate-100 dark:bg-gray-800 dark:hover:bg-gray-700 text-slate-800 dark:text-white font-bold text-xs px-3 py-2 rounded-xl border border-slate-200 dark:border-gray-700 flex items-center gap-1.5"
                      >
                        <Layers className="w-3.5 h-3.5" />
                        <span>{n}-Game Slip</span>
                      </button>
                    ))}
                    <button
                      onClick={() => setActiveTab("accuracy")}
                      className="text-slate-600 dark:text-gray-300 hover:text-emerald-700 dark:hover:text-emerald-400 text-xs font-semibold px-2 py-2 flex items-center gap-1"
                    >
                      <BarChart2 className="w-3.5 h-3.5" />
                      <span>How accurate are we?</span>
                    </button>
                  </div>
                </div>
              </div>

              {/* Data status */}
              <div className="bg-slate-100 dark:bg-gray-900/50 border border-slate-200 dark:border-gray-800 rounded-xl p-3 flex flex-wrap items-center justify-between gap-2.5 text-xs text-slate-700 dark:text-gray-300">
                <span>
                  <b>{fixtures.length}</b> upcoming matches in {leagues.length - 1} leagues • predictions refresh every 3 hours
                </span>
                <button
                  onClick={fetchFixtures}
                  disabled={loading}
                  className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-[11px]"
                >
                  <RefreshCw className={`w-3 h-3 ${loading ? "animate-spin" : ""}`} />
                  <span>Refresh</span>
                </button>
              </div>

              {/* Filters */}
              <div className="space-y-2">
                <div className="flex items-center gap-1.5 overflow-x-auto pb-1 no-scrollbar text-xs">
                  {leagues.map((lg) => (
                    <button
                      key={lg}
                      onClick={() => setSelectedLeague(lg)}
                      className={`px-3 py-1.5 rounded-lg font-bold whitespace-nowrap text-xs ${
                        selectedLeague === lg
                          ? "bg-emerald-600 text-white dark:bg-emerald-500 dark:text-black shadow-sm"
                          : "bg-white dark:bg-gray-900 border border-slate-200 dark:border-gray-800 text-slate-600 dark:text-gray-400 hover:text-slate-900 dark:hover:text-white"
                      }`}
                    >
                      {lg === "All" ? "All" : `${lg} (${leagueCounts[lg]})`}
                    </button>
                  ))}
                </div>

                <div className="flex items-center justify-between text-xs text-slate-500 dark:text-gray-400 border-t border-slate-200 dark:border-gray-800/60 pt-2 flex-wrap gap-2">
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <span className="text-[11px] font-bold uppercase text-slate-400 dark:text-gray-500">Confidence:</span>
                    {[
                      { key: "All", label: "All matches" },
                      { key: "Bankers", label: "🟢 70%+" },
                      { key: "Favorites", label: "🟡 58%+" },
                    ].map((c) => (
                      <button
                        key={c.key}
                        onClick={() => setSelectedConfidence(c.key)}
                        className={`px-2.5 py-1 rounded text-[11px] font-bold border ${
                          selectedConfidence === c.key
                            ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-500/20 dark:text-emerald-300 border-emerald-300 dark:border-emerald-500/40"
                            : "bg-white dark:bg-gray-900 text-slate-600 dark:text-gray-400 border-slate-200 dark:border-gray-800"
                        }`}
                      >
                        {c.label}
                      </button>
                    ))}
                  </div>
                  <span className="text-[11px]">Showing <b>{filteredFixtures.length}</b> of {fixtures.length}</span>
                </div>
              </div>

              {/* Match cards */}
              {loading && fixtures.length === 0 ? (
                <div className="text-center py-16 space-y-3">
                  <RefreshCw className="w-8 h-8 text-emerald-600 dark:text-emerald-400 animate-spin mx-auto" />
                  <p className="text-slate-500 dark:text-gray-400 text-xs">Loading predictions...</p>
                </div>
              ) : loadError && fixtures.length === 0 ? (
                <p className="text-center py-16 text-sm text-slate-500 dark:text-gray-400">
                  Couldn&apos;t reach the prediction server. Please try again shortly.
                </p>
              ) : filteredFixtures.length === 0 ? (
                <p className="text-center py-16 text-sm text-slate-500 dark:text-gray-400">No matches for these filters.</p>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5 sm:gap-4">
                  {filteredFixtures.map((fixture) => (
                    <MatchCard
                      key={fixture.id}
                      fixture={fixture}
                      onSelectBet={handleSelectBet}
                      isSelected={selectedBets.some((b) =>
                        fixture.prediction?.value_bets.some((vb) => vb.market_name === b.market_name)
                      )}
                    />
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === "bankroll" && showKelly && (
            <KellyCalculator
              bankroll={bankroll}
              onBankrollChange={setBankroll}
              selectedBets={selectedBets}
              onRemoveBet={handleRemoveBet}
            />
          )}

          {activeTab === "tracker" && <TrackRecordView stats={trackStats} verification={verification} />}

          {activeTab === "accuracy" && <AccuracyView report={modelReport} />}
        </main>

        <MobileBottomNav
          activeTab={activeTab}
          onSelectTab={setActiveTab}
          onOpenBankerModal={loadDailyBanker}
          onOpenAccaBuilder={(count) => buildMultiGameAcca(count)}
          showKelly={showKelly}
        />

        <footer className="border-t border-slate-200 dark:border-gray-800/80 bg-slate-100/60 dark:bg-[#070b13] py-6 px-4 text-xs text-slate-500 dark:text-gray-500 text-center">
          <div className="max-w-3xl mx-auto space-y-2">
            <p className="text-slate-600 dark:text-gray-400 font-semibold">
              18+ only. Predictions are probabilities, not guarantees. Never bet more than you can afford to lose.
            </p>
            <p>
              LivelyBorg AI is an independent prediction service. We are not a bookmaker, do not accept bets, and are not
              affiliated with SportyBet, Bet9ja or any other bookmaker.
            </p>
            <p>
              If gambling stops being fun, take a break and talk to someone you trust, or visit{" "}
              <a href="https://www.begambleaware.org" target="_blank" rel="noopener noreferrer" className="underline">
                begambleaware.org
              </a>{" "}
              for free, confidential support.
            </p>
            <p className="text-[11px] text-slate-400 dark:text-gray-600">
              Data: football-data.co.uk and football-data.org. © 2026 LivelyBorg Technologies.
            </p>
          </div>
        </footer>

        {showBankerModal && (
          <SmartAccaModal
            data={bankerData}
            bankroll={bankroll}
            onClose={() => setShowBankerModal(false)}
            onOpenShareModal={() => {
              setShowBankerModal(false);
              setShowShareModal(true);
            }}
            onRebuildAcca={buildMultiGameAcca}
            isLoading={accaLoading}
          />
        )}

        {showShareModal && <WhatsAppSlipGenerator data={bankerData} onClose={() => setShowShareModal(false)} />}
      </div>
    </AgeGate>
  );
}
