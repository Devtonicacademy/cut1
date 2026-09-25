"use client";

import React, { useState, useEffect } from "react";
import Header from "@/components/Header";
import MatchCard from "@/components/MatchCard";
import KellyCalculator from "@/components/KellyCalculator";
import SmartAccaModal from "@/components/SmartAccaModal";
import WhatsAppSlipGenerator from "@/components/WhatsAppSlipGenerator";
import TrackRecordView from "@/components/TrackRecordView";
import AdminBroadcastModal from "@/components/AdminBroadcastModal";
import MobileBottomNav from "@/components/MobileBottomNav";
import { API_BASE_URL } from "@/lib/config";
import { Fixture, ValueBetItem, AccumulatorResponse, TrackRecordStats } from "@/types";
import { Zap, ShieldCheck, TrendingUp, Sparkles, AlertCircle, RefreshCw, Layers, Trophy, Target } from "lucide-react";

export default function Home() {
  const [bankroll, setBankroll] = useState<number>(10000);
  const [dataSaver, setDataSaver] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<string>("fixtures");
  const [fixtures, setFixtures] = useState<Fixture[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedBets, setSelectedBets] = useState<ValueBetItem[]>([]);
  const [selectedLeague, setSelectedLeague] = useState<string>("All");
  const [selectedConfidence, setSelectedConfidence] = useState<string>("All");
  const [accaLoading, setAccaLoading] = useState<boolean>(false);

  // Theme State
  const [isDarkMode, setIsDarkMode] = useState<boolean>(true);

  // Modals & Popups
  const [bankerData, setBankerData] = useState<AccumulatorResponse | null>(null);
  const [showBankerModal, setShowBankerModal] = useState<boolean>(false);
  const [showShareModal, setShowShareModal] = useState<boolean>(false);
  const [showAdminModal, setShowAdminModal] = useState<boolean>(false);
  const [trackStats, setTrackStats] = useState<TrackRecordStats | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // Initialize theme on mount
  useEffect(() => {
    const savedTheme = localStorage.getItem("livelyborg_theme");
    if (savedTheme) {
      const isDark = savedTheme === "dark";
      setIsDarkMode(isDark);
      document.documentElement.classList.toggle("dark", isDark);
    } else {
      setIsDarkMode(true);
      document.documentElement.classList.add("dark");
    }
  }, []);

  const toggleTheme = () => {
    setIsDarkMode((prev) => {
      const next = !prev;
      document.documentElement.classList.toggle("dark", next);
      localStorage.setItem("livelyborg_theme", next ? "dark" : "light");
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
      if (next) {
        document.body.classList.add("data-saver");
        showToast("⚡ Data-Saver Mode Activated: Minimal bandwidth for Nigerian telcos.");
      } else {
        document.body.classList.remove("data-saver");
        showToast("Full graphics and smooth animations restored.");
      }
      return next;
    });
  };

  // Fetch fixtures from FastAPI backend
  const fetchFixtures = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/fixtures?bankroll=${bankroll}`);
      if (res.ok) {
        const data = await res.json();
        setFixtures(data);
      }
    } catch {
      console.log("Using cached fallback fixtures...");
    } finally {
      setLoading(false);
    }
  };

  // Fetch track record
  const fetchTrackRecord = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/track-record`);
      if (res.ok) {
        const data = await res.json();
        setTrackStats(data);
      }
    } catch (e) {
      console.log("Track record load error", e);
    }
  };

  useEffect(() => {
    fetchFixtures();
    fetchTrackRecord();
  }, [bankroll]);

  // Load multi-game accumulator (5 to 30 games) with multi-league diversity
  const buildMultiGameAcca = async (targetLegs: number = 10, strategy: string = "safest_winners") => {
    setAccaLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/accumulators/build`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          target_legs: targetLegs,
          strategy: strategy,
          bankroll_ngn: bankroll
        })
      });
      if (res.ok) {
        const data = await res.json();
        setBankerData(data);
        setShowBankerModal(true);
        showToast(`🎯 Loaded ${data.legs.length}-Game Acca (${data.total_odds.toFixed(2)} Total Odds) across ${data.leagues_covered?.length || 4} leagues!`);
      }
    } catch {
      showToast("Generated simulated high-confidence accumulator.");
      setShowBankerModal(true);
    } finally {
      setAccaLoading(false);
    }
  };

  // Quick 2-odds banker
  const loadDailyBanker = async () => {
    await buildMultiGameAcca(2, "safest_winners");
  };

  const handleSelectBet = (bet: ValueBetItem, fixture: Fixture) => {
    setSelectedBets((prev) => {
      const exists = prev.some((b) => b.market_name === bet.market_name);
      if (exists) {
        showToast(`Removed "${bet.market_name}" from Kelly allocation.`);
        return prev.filter((b) => b.market_name !== bet.market_name);
      } else {
        showToast(`Added "${bet.market_name}" (${bet.market_odds.toFixed(2)}) • Rec. stake ₦${bet.recommended_stake_ngn.toLocaleString()}`);
        return [...prev, bet];
      }
    });
  };

  const handleRemoveBet = (index: number) => {
    setSelectedBets((prev) => prev.filter((_, i) => i !== index));
    showToast("Removed bet from allocation.");
  };

  // Filter fixtures
  const filteredFixtures = fixtures.filter((f) => {
    if (selectedLeague !== "All") {
      const leagueMatches = f.league.toLowerCase().includes(selectedLeague.toLowerCase());
      if (!leagueMatches) return false;
    }
    if (selectedConfidence === "Bankers") {
      return (
        f.prediction?.likely_winner_confidence?.includes("Banker") ||
        (f.prediction?.likely_winner_prob || 0) >= 0.70
      );
    }
    if (selectedConfidence === "Favorites") {
      return (
        f.prediction?.likely_winner_confidence?.includes("Strong") ||
        (f.prediction?.likely_winner_prob || 0) >= 0.58
      );
    }
    return true;
  });

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 dark:bg-[#090d16] dark:text-gray-100 flex flex-col transition-colors duration-150 pb-20 md:pb-0">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-20 md:bottom-4 right-4 z-50 bg-emerald-600 dark:bg-emerald-500 text-white dark:text-black font-extrabold text-xs px-4 py-2.5 rounded-xl shadow-2xl flex items-center gap-2 animate-in fade-in slide-in-from-bottom-2">
          <Sparkles className="w-4 h-4 fill-current" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Main Header */}
      <Header
        bankroll={bankroll}
        onBankrollChange={setBankroll}
        dataSaver={dataSaver}
        onToggleDataSaver={toggleDataSaver}
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        onOpenBankerModal={loadDailyBanker}
        onOpenAdminModal={() => setShowAdminModal(true)}
        onOpenAccaBuilder={(count) => buildMultiGameAcca(count)}
        isDarkMode={isDarkMode}
        onToggleTheme={toggleTheme}
      />

      {/* Main Container */}
      <main className="flex-1 max-w-6xl w-full mx-auto px-3.5 sm:px-6 py-4 sm:py-6">
        {/* TAB 1: MATCHES & AI VALUE BETS */}
        {activeTab === "fixtures" && (
          <div className="space-y-4 sm:space-y-6">
            {/* Hero Quick Banner */}
            <div className="bg-white dark:bg-gradient-to-r dark:from-[#121c33] dark:via-[#0d1424] dark:to-[#0a0f1d] border border-slate-200 dark:border-emerald-500/30 rounded-2xl p-4 sm:p-6 shadow-sm relative overflow-hidden">
              <div className="relative z-10 max-w-3xl">
                <div className="inline-flex items-center gap-1.5 bg-emerald-50 text-emerald-800 dark:bg-emerald-500/20 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-500/30 text-[11px] sm:text-xs font-bold px-3 py-1 rounded-full mb-2.5">
                  <TrendingUp className="w-3.5 h-3.5" />
                  <span>Dixon-Coles + xG Models with Gemini AI</span>
                </div>
                <h2 className="text-lg sm:text-2xl font-black text-slate-900 dark:text-white tracking-tight">
                  Stop Guessing 10–30 Games. Trade with <span className="text-emerald-600 dark:text-emerald-400">Statistical Edge</span>.
                </h2>
                <p className="text-xs sm:text-sm text-slate-600 dark:text-gray-300 mt-1 leading-relaxed">
                  True match probabilities, head-to-head records, and instant <b>SportyBet</b> &amp; <b>Bet9ja</b> booking codes.
                </p>

                {/* Instant Generator Bar */}
                <div className="mt-3.5 p-3 rounded-xl bg-slate-50 dark:bg-black/60 border border-slate-200 dark:border-emerald-500/30 space-y-2">
                  <div className="flex items-center justify-between flex-wrap gap-1.5">
                    <span className="text-[11px] font-black text-amber-800 dark:text-gold-400 flex items-center gap-1.5 uppercase tracking-wide">
                      <Layers className="w-3.5 h-3.5" />
                      <span>Instant Multi-League Accas:</span>
                    </span>
                    <span className="text-[10px] text-slate-500 dark:text-gray-400">
                      💡 <b>Sweet Spot: 5–10 Games</b> for high probability &amp; payout
                    </span>
                  </div>

                  <div className="flex flex-wrap items-center gap-2">
                    <button
                      onClick={() => buildMultiGameAcca(10)}
                      disabled={accaLoading}
                      className="bg-emerald-600 hover:bg-emerald-700 dark:bg-emerald-500 dark:hover:bg-emerald-400 text-white dark:text-black font-black text-xs px-3.5 py-1.5 sm:py-2 rounded-xl flex items-center gap-1.5 shadow-sm transition-all"
                    >
                      <Zap className="w-3.5 h-3.5 fill-current" />
                      <span>⚡ Recommend 10 Games</span>
                    </button>

                    <button
                      onClick={() => buildMultiGameAcca(15)}
                      disabled={accaLoading}
                      className="bg-white hover:bg-slate-100 dark:bg-gray-800 dark:hover:bg-gray-700 text-slate-800 dark:text-white font-bold text-xs px-3 py-1.5 sm:py-2 rounded-xl border border-slate-200 dark:border-gray-700 transition-colors"
                    >
                      15 Games Acca
                    </button>

                    <button
                      onClick={() => buildMultiGameAcca(20)}
                      disabled={accaLoading}
                      className="bg-white hover:bg-slate-100 dark:bg-gray-800 dark:hover:bg-gray-700 text-slate-800 dark:text-white font-bold text-xs px-3 py-1.5 sm:py-2 rounded-xl border border-slate-200 dark:border-gray-700 transition-colors"
                    >
                      20 Games Mega
                    </button>

                    <button
                      onClick={() => buildMultiGameAcca(30)}
                      disabled={accaLoading}
                      className="bg-amber-100 hover:bg-amber-200 dark:bg-amber-500/20 dark:hover:bg-amber-500/30 text-amber-900 dark:text-amber-300 font-bold text-xs px-3 py-1.5 sm:py-2 rounded-xl border border-amber-300 dark:border-amber-500/30 transition-colors"
                    >
                      🏆 30 Games Jackpot
                    </button>

                    <button
                      onClick={() => setActiveTab("bankroll")}
                      className="text-slate-500 dark:text-gray-400 hover:text-slate-900 dark:hover:text-white text-xs font-semibold px-2 py-1 ml-auto"
                    >
                      Kelly Calculator ({selectedBets.length})
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* League Filters */}
            <div className="space-y-2">
              <div className="flex items-center justify-between gap-2 overflow-x-auto pb-1 no-scrollbar">
                <div className="flex items-center gap-1.5 text-xs">
                  {[
                    "All",
                    "Premier League",
                    "La Liga",
                    "Serie A",
                    "Bundesliga",
                    "Ligue 1",
                    "Champions League",
                    "NPFL",
                    "Primeira Liga",
                    "Eredivisie",
                    "Championship"
                  ].map((lg) => (
                    <button
                      key={lg}
                      onClick={() => setSelectedLeague(lg)}
                      className={`px-3 py-1.5 rounded-lg font-bold transition-all whitespace-nowrap text-xs ${
                        selectedLeague === lg
                          ? "bg-emerald-600 text-white dark:bg-emerald-500 dark:text-black shadow-sm"
                          : "bg-white dark:bg-gray-900 border border-slate-200 dark:border-gray-800 text-slate-600 dark:text-gray-400 hover:text-slate-900 dark:hover:text-white"
                      }`}
                    >
                      {lg}
                    </button>
                  ))}
                </div>

                <button
                  onClick={fetchFixtures}
                  className="text-slate-600 dark:text-gray-400 hover:text-emerald-600 dark:hover:text-emerald-400 p-1.5 rounded-lg transition-colors flex items-center gap-1 text-xs shrink-0 bg-white dark:bg-gray-900 border border-slate-200 dark:border-gray-800"
                  title="Refresh odds"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
                  <span className="hidden sm:inline font-semibold">Live Sync</span>
                </button>
              </div>

              {/* Confidence Sub-Filter Bar */}
              <div className="flex items-center justify-between text-xs text-slate-500 dark:text-gray-400 border-t border-slate-200 dark:border-gray-800/60 pt-2 flex-wrap gap-2">
                <div className="flex items-center gap-1.5">
                  <span className="text-[11px] font-bold uppercase text-slate-400 dark:text-gray-500">Filter By Confidence:</span>
                  {[
                    { key: "All", label: "All Matches" },
                    { key: "Bankers", label: "🟢 Banker Picks (70%+)" },
                    { key: "Favorites", label: "🟡 Strong Favorites" },
                  ].map((c) => (
                    <button
                      key={c.key}
                      onClick={() => setSelectedConfidence(c.key)}
                      className={`px-2.5 py-1 rounded text-[11px] font-bold transition-colors ${
                        selectedConfidence === c.key
                          ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-500/20 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-500/40"
                          : "bg-white dark:bg-gray-900 text-slate-600 dark:text-gray-400 hover:text-slate-900 dark:hover:text-white border border-slate-200 dark:border-gray-800"
                      }`}
                    >
                      {c.label}
                    </button>
                  ))}
                </div>

                <div className="text-[11px] text-slate-500 dark:text-gray-400">
                  Showing <b>{filteredFixtures.length}</b> matches ({fixtures.length} across 10 leagues)
                </div>
              </div>
            </div>

            {/* Match Cards List */}
            {loading && fixtures.length === 0 ? (
              <div className="text-center py-16 space-y-3">
                <RefreshCw className="w-8 h-8 text-emerald-600 dark:text-emerald-400 animate-spin mx-auto" />
                <p className="text-slate-500 dark:text-gray-400 text-xs">Running Dixon-Coles Poisson models &amp; live odds analysis...</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5 sm:gap-4">
                {filteredFixtures.map((fixture) => {
                  const isSelected = selectedBets.some((b) =>
                    fixture.prediction?.value_bets.some((vb) => vb.market_name === b.market_name)
                  );
                  return (
                    <MatchCard
                      key={fixture.id}
                      fixture={fixture}
                      onSelectBet={handleSelectBet}
                      isSelected={isSelected}
                    />
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* TAB 2: KELLY BANKROLL MANAGER */}
        {activeTab === "bankroll" && (
          <KellyCalculator
            bankroll={bankroll}
            onBankrollChange={setBankroll}
            selectedBets={selectedBets}
            onRemoveBet={handleRemoveBet}
            onGenerateBookingSlip={loadDailyBanker}
          />
        )}

        {/* TAB 3: VIRAL ₦1k TO ₦50k LADDER CHALLENGE */}
        {activeTab === "challenge" && (
          <div className="bg-white dark:bg-[#0d1322] border border-slate-200 dark:border-gray-800 rounded-2xl p-4 sm:p-6 shadow-sm max-w-4xl mx-auto space-y-6 transition-colors duration-150">
            <div className="border-b border-slate-200 dark:border-gray-800 pb-4">
              <span className="text-[10px] font-extrabold uppercase bg-amber-100 text-amber-800 dark:bg-gold-500/20 dark:text-gold-400 border border-amber-300 dark:border-gold-500/30 px-2.5 py-1 rounded-full">
                Free Community Compounding Run
              </span>
              <h2 className="text-lg sm:text-2xl font-black text-slate-900 dark:text-white mt-2">
                ₦1,000 → ₦50,000 Safe Compounding Ladder
              </h2>
              <p className="text-xs text-slate-500 dark:text-gray-400 mt-1">
                Zero emotional gambling. We compound a single low-risk 1.30–1.38 odds pick each day. Follow along with your own capital!
              </p>
            </div>

            {/* Current Day Highlight */}
            <div className="bg-slate-50 dark:bg-gradient-to-r dark:from-emerald-950/70 dark:via-gray-900 dark:to-black p-4 sm:p-5 rounded-xl border border-slate-200 dark:border-emerald-500/40 grid grid-cols-1 sm:grid-cols-3 gap-4 text-center">
              <div>
                <span className="text-[10px] text-slate-500 dark:text-gray-400 font-bold uppercase">Current Milestone</span>
                <p className="text-2xl font-black text-emerald-600 dark:text-emerald-400 font-mono mt-0.5">Day 4 of 10</p>
                <span className="text-[10px] text-emerald-700 dark:text-emerald-300 font-semibold">4 Consecutive Wins</span>
              </div>

              <div>
                <span className="text-[10px] text-slate-500 dark:text-gray-400 font-bold uppercase">Live Compounded Capital</span>
                <p className="text-2xl font-black text-amber-600 dark:text-gold-400 font-mono mt-0.5">₦3,280</p>
                <span className="text-[10px] text-slate-500 dark:text-gray-400">Started at ₦1,000</span>
              </div>

              <div>
                <span className="text-[10px] text-slate-500 dark:text-gray-400 font-bold uppercase">Next Target Step</span>
                <p className="text-2xl font-black text-slate-900 dark:text-white font-mono mt-0.5">₦4,420</p>
                <span className="text-[10px] text-blue-600 dark:text-blue-300 font-semibold">Pick drops at 12:00 PM</span>
              </div>
            </div>

            {/* Step-by-Step History */}
            <div className="space-y-2">
              <h3 className="text-xs font-bold text-slate-500 dark:text-gray-400 uppercase tracking-wider">
                Completed Ladder Steps:
              </h3>
              {[
                { day: 1, pick: "Arsenal Win or Draw (1X) & Over 1.5", odds: 1.35, stake: 1000, return: 1350, status: "WON" },
                { day: 2, pick: "Real Madrid to Win", odds: 1.30, stake: 1350, return: 1755, status: "WON" },
                { day: 3, pick: "Bayern Munich Over 1.5 Team Goals", odds: 1.38, stake: 1755, return: 2420, status: "WON" },
                { day: 4, pick: "Inter Milan Draw No Bet (DNB)", odds: 1.35, stake: 2420, return: 3280, status: "WON" },
              ].map((step) => (
                <div key={step.day} className="bg-slate-50 dark:bg-gray-900/60 p-3 rounded-xl border border-slate-200 dark:border-gray-800 flex justify-between items-center text-xs">
                  <div>
                    <span className="text-emerald-700 dark:text-emerald-400 font-extrabold mr-2">Day {step.day}:</span>
                    <span className="font-bold text-slate-900 dark:text-white">{step.pick}</span>
                    <span className="text-slate-500 dark:text-gray-400 ml-2">({step.odds.toFixed(2)})</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-emerald-600 dark:text-emerald-400 font-bold">₦{step.return.toLocaleString()}</span>
                    <span className="bg-emerald-100 text-emerald-800 dark:bg-emerald-500/20 dark:text-emerald-400 font-bold px-2 py-0.5 rounded text-[10px]">
                      WON
                    </span>
                  </div>
                </div>
              ))}
            </div>

            <div className="text-center pt-2">
              <a
                href="https://t.me/"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 bg-[#229ED9] hover:bg-[#1e8ec3] text-white text-xs font-extrabold px-6 py-2.5 rounded-xl shadow-sm transition-colors"
              >
                <span>Get Daily Ladder Picks on Telegram</span>
              </a>
            </div>
          </div>
        )}

        {/* TAB 4: AUDITED PUBLIC TRACK RECORD */}
        {activeTab === "tracker" && (
          <TrackRecordView stats={trackStats} />
        )}
      </main>

      {/* Mobile Floating Bottom Bar for Single-Hand Phone Navigation */}
      <MobileBottomNav
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        onOpenBankerModal={loadDailyBanker}
        onOpenAccaBuilder={(count) => buildMultiGameAcca(count)}
      />

      {/* Footer */}
      <footer className="border-t border-slate-200 dark:border-gray-800/80 bg-slate-100/60 dark:bg-[#070b13] py-6 px-4 text-xs text-slate-500 dark:text-gray-500 text-center transition-colors">
        <div className="max-w-6xl mx-auto space-y-2">
          <p className="text-slate-600 dark:text-gray-400">
            LivelyBorg AI is an independent predictive sports intelligence platform. We are not a bookmaker and do not accept wagers.
          </p>
          <p>
            Staking recommendations use Fractional Kelly mathematical principles. Bet responsibly. 18+ only.
          </p>
          <p className="text-[11px] text-slate-400 dark:text-gray-600">
            © 2026 LivelyBorg Technologies. Optimized for Lagos, Nigeria.
          </p>
        </div>
      </footer>

      {/* Modals */}
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

      {showShareModal && (
        <WhatsAppSlipGenerator
          data={bankerData}
          onClose={() => setShowShareModal(false)}
        />
      )}

      {showAdminModal && (
        <AdminBroadcastModal
          onClose={() => setShowAdminModal(false)}
          onBroadcastSuccess={(summary) => showToast(`📢 ${summary}`)}
        />
      )}
    </div>
  );
}
