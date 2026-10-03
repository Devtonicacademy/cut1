"use client";

import React, { useMemo } from "react";
import FilterSidebar from "@/components/FilterSidebar";
import GlassCard from "@/components/ui/GlassCard";
import Chip from "@/components/ui/Chip";
import { MockFixture, useFixtureFilters } from "@/lib/fixtureFilters";

/** Builds kick-offs relative to now, so "Today" / "Tomorrow" always have matches. */
function buildMockFixtures(): MockFixture[] {
  const at = (days: number, hour: number) => {
    const d = new Date();
    d.setDate(d.getDate() + days);
    d.setHours(hour, 0, 0, 0);
    return d.toISOString();
  };
  return [
    { id: "1", league: "Premier League", home: "Arsenal", away: "Chelsea", kickoff: at(0, 17) },
    { id: "2", league: "Premier League", home: "Liverpool", away: "Everton", kickoff: at(1, 15) },
    { id: "3", league: "Premier League", home: "Man City", away: "Brighton", kickoff: at(3, 16) },
    { id: "4", league: "La Liga", home: "Barcelona", away: "Sevilla", kickoff: at(0, 20) },
    { id: "5", league: "La Liga", home: "Real Madrid", away: "Valencia", kickoff: at(2, 21) },
    { id: "6", league: "Serie A", home: "Inter", away: "Roma", kickoff: at(1, 19) },
    { id: "7", league: "Serie A", home: "Juventus", away: "Napoli", kickoff: at(5, 20) },
    { id: "8", league: "Bundesliga", home: "Bayern", away: "Dortmund", kickoff: at(0, 18) },
    { id: "9", league: "Bundesliga", home: "Leipzig", away: "Leverkusen", kickoff: at(9, 15) },
    { id: "10", league: "Ligue 1", home: "PSG", away: "Lyon", kickoff: at(4, 21) },
  ];
}

const fmt = (iso: string) =>
  new Date(iso).toLocaleString(undefined, { weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });

export default function SidebarDemo() {
  const fixtures = useMemo(buildMockFixtures, []);
  const { filters, visible, leagueCounts, activeCount, toggleLeague, setDatePreset, setCustomDate, reset } =
    useFixtureFilters(fixtures);

  return (
    <main className="mx-auto w-full max-w-6xl px-3.5 py-6 sm:px-6">
      <h1 className="mb-4 font-display text-xl font-bold text-slate-900 dark:text-white">Fixtures</h1>

      <div className="flex flex-col items-start gap-4 lg:flex-row lg:gap-6">
        <FilterSidebar
          leagues={leagueCounts}
          filters={filters}
          activeCount={activeCount}
          onToggleLeague={toggleLeague}
          onDatePreset={setDatePreset}
          onCustomDate={setCustomDate}
          onReset={reset}
        />
        <section className="w-full min-w-0 flex-1 space-y-3" aria-live="polite">
          <p className="font-mono text-xs text-slate-500 dark:text-gray-400">
            Showing {visible.length} of {fixtures.length} matches
          </p>
          {visible.length === 0 ? (
            <GlassCard className="p-8 text-center text-sm text-slate-500 dark:text-gray-400">
              No matches for these filters.{" "}
              <button onClick={reset} className="font-bold text-emerald-500 hover:underline">
                Clear filters
              </button>
            </GlassCard>
          ) : (
            visible.map((m) => (
              <GlassCard key={m.id} className="flex items-center justify-between gap-3 p-4">
                <div>
                  <Chip tone="success" className="mb-1.5 uppercase tracking-wider">
                    {m.league}
                  </Chip>
                  <p className="font-display text-base font-semibold text-slate-900 dark:text-white">
                    {m.home} <span className="text-slate-400">vs</span> {m.away}
                  </p>
                </div>
                <span className="shrink-0 font-mono text-xs text-slate-500 dark:text-gray-400">{fmt(m.kickoff)}</span>
              </GlassCard>
            ))
          )}
        </section>
      </div>
    </main>
  );
}
