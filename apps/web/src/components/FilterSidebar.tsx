"use client";

import React, { useEffect, useId, useState } from "react";
import { CalendarDays, ChevronDown, Filter, X } from "lucide-react";
import { DatePreset, FixtureFilters } from "@/lib/fixtureFilters";

interface FilterSidebarProps {
  leagues: { league: string; count: number }[];
  filters: FixtureFilters;
  activeCount: number;
  onToggleLeague: (league: string) => void;
  onDatePreset: (preset: DatePreset) => void;
  onCustomDate: (date: string) => void;
  onReset: () => void;
}

const DATE_OPTIONS: { value: DatePreset; label: string }[] = [
  { value: "today", label: "Today" },
  { value: "tomorrow", label: "Tomorrow" },
  { value: "week", label: "This Week" },
];

/**
 * Filter panel for the fixtures list. A sticky column from `lg` up; below that it sits
 * behind a "Filters" button and slides in as a drawer. Fully controlled by its parent.
 */
export default function FilterSidebar({
  leagues,
  filters,
  activeCount,
  onToggleLeague,
  onDatePreset,
  onCustomDate,
  onReset,
}: FilterSidebarProps) {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [leaguesOpen, setLeaguesOpen] = useState(true);
  const uid = useId();

  // Close the drawer with Escape and stop the page scrolling behind it.
  useEffect(() => {
    if (!drawerOpen) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setDrawerOpen(false);
    document.addEventListener("keydown", onKey);
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = prev;
    };
  }, [drawerOpen]);

  // The panel is rendered twice (desktop column + mobile drawer), so ids and radio groups are scoped per copy.
  const renderPanel = (scope: string) => (
    <div className="space-y-5">
      {/* League filter (collapsible) */}
      <section>
        <button
          onClick={() => setLeaguesOpen((o) => !o)}
          aria-expanded={leaguesOpen}
          aria-controls={`${uid}-${scope}-leagues`}
          className="flex w-full items-center justify-between text-left font-display text-sm font-semibold text-slate-900 dark:text-white"
        >
          Filter by League
          <ChevronDown className={`h-4 w-4 text-slate-500 transition-transform dark:text-gray-400 ${leaguesOpen ? "rotate-180" : ""}`} />
        </button>
        {leaguesOpen && (
          <ul id={`${uid}-${scope}-leagues`} className="mt-2 space-y-0.5">
            {leagues.map(({ league, count }) => {
              const checked = filters.leagues.includes(league);
              return (
                <li key={league}>
                  <label
                    className={`flex cursor-pointer items-center gap-2.5 rounded-lg px-2 py-1.5 text-sm transition-colors hover:bg-slate-100 dark:hover:bg-slate-800 ${
                      count === 0 && !checked ? "opacity-50" : ""
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={() => onToggleLeague(league)}
                      className="h-4 w-4 shrink-0 cursor-pointer rounded accent-emerald-500"
                    />
                    <span className="flex-1 text-slate-700 dark:text-gray-200">{league}</span>
                    <span className="rounded-chip border border-slate-200 px-1.5 font-mono text-[10px] font-semibold text-slate-500 dark:border-glass dark:text-gray-400">
                      {count}
                    </span>
                  </label>
                </li>
              );
            })}
          </ul>
        )}
      </section>

      {/* Date filter */}
      <fieldset>
        <legend className="mb-2 font-display text-sm font-semibold text-slate-900 dark:text-white">Filter by Date</legend>
        <div className="space-y-0.5">
          {DATE_OPTIONS.map((o) => (
            <label
              key={o.value}
              className="flex cursor-pointer items-center gap-2.5 rounded-lg px-2 py-1.5 text-sm text-slate-700 transition-colors hover:bg-slate-100 dark:text-gray-200 dark:hover:bg-slate-800"
            >
              <input
                type="radio"
                name={`${uid}-${scope}-date`}
                checked={filters.datePreset === o.value}
                onChange={() => onDatePreset(o.value)}
                className="h-4 w-4 cursor-pointer accent-emerald-500"
              />
              {o.label}
            </label>
          ))}
        </div>

        <label className="mt-2 block px-2">
          <span className="mb-1 flex items-center gap-1.5 text-xs text-slate-500 dark:text-gray-400">
            <CalendarDays className="h-3.5 w-3.5" />
            Custom date
          </span>
          <input
            type="date"
            value={filters.customDate}
            onChange={(e) => onCustomDate(e.target.value)}
            className={`w-full rounded-lg border px-2.5 py-1.5 font-mono text-xs ${
              filters.datePreset === "custom"
                ? "border-emerald-500 text-slate-900 dark:text-white"
                : "border-slate-200 text-slate-600 dark:border-white/[0.1] dark:text-gray-300"
            }`}
          />
        </label>
      </fieldset>

      <button
        onClick={onReset}
        disabled={activeCount === 0}
        className="w-full rounded-lg border border-slate-200 bg-slate-100 py-2 text-xs font-bold text-slate-700 transition-colors hover:bg-slate-200 disabled:cursor-not-allowed disabled:opacity-40 dark:border-glass dark:bg-slate-800 dark:text-gray-200 dark:hover:bg-slate-700"
      >
        Clear filters
      </button>
    </div>
  );

  return (
    <div className="lg:w-64 lg:shrink-0">
      {/* Mobile / tablet trigger */}
      <button
        onClick={() => setDrawerOpen(true)}
        className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs font-bold text-slate-700 shadow-sm dark:border-glass dark:bg-surface-glass dark:text-gray-200 lg:hidden"
      >
        <Filter className="h-4 w-4" />
        Filters
        {activeCount > 0 && (
          <span className="rounded-full bg-emerald-500 px-1.5 font-mono text-[10px] font-semibold text-black">{activeCount}</span>
        )}
      </button>

      {/* Desktop: sticky column */}
      <aside
        aria-label="Fixture filters"
        className="sticky top-4 hidden rounded-panel border border-slate-200 bg-white p-4 shadow-sm dark:border-glass dark:bg-surface-glass dark:shadow-none dark:backdrop-blur-glass lg:block"
      >
        {renderPanel("side")}
      </aside>

      {/* Mobile / tablet: drawer */}
      {drawerOpen && (
        <div className="fixed inset-0 z-50 lg:hidden" role="dialog" aria-modal="true" aria-label="Fixture filters">
          <div className="absolute inset-0 bg-black/60" onClick={() => setDrawerOpen(false)} />
          <div className="absolute inset-y-0 left-0 flex w-[85%] max-w-xs flex-col border-r border-slate-200 bg-white p-4 dark:border-white/[0.12] dark:bg-surface-modal dark:shadow-modal dark:backdrop-blur-modal">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="font-display text-base font-semibold text-slate-900 dark:text-white">Filters</h2>
              <button
                onClick={() => setDrawerOpen(false)}
                aria-label="Close filters"
                className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100 dark:text-gray-400 dark:hover:bg-slate-800"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto">{renderPanel("drawer")}</div>
            <button
              onClick={() => setDrawerOpen(false)}
              className="mt-4 w-full rounded-lg bg-emerald-500 py-2.5 text-sm font-bold text-black hover:bg-emerald-600"
            >
              Show results
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
