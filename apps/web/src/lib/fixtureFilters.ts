import { useMemo, useState } from "react";

export interface MockFixture {
  id: string;
  league: string;
  home: string;
  away: string;
  /** ISO timestamp of kick-off. */
  kickoff: string;
}

export type DatePreset = "all" | "today" | "tomorrow" | "week" | "custom";

export interface FixtureFilters {
  leagues: string[];
  datePreset: DatePreset;
  /** YYYY-MM-DD, used when datePreset is "custom". */
  customDate: string;
}

export const DEFAULT_FILTERS: FixtureFilters = { leagues: [], datePreset: "all", customDate: "" };

const DAY_MS = 24 * 60 * 60 * 1000;

const startOfDay = (d: Date) => new Date(d.getFullYear(), d.getMonth(), d.getDate());

/** Local YYYY-MM-DD, matching the value of <input type="date">. */
export const toDateKey = (d: Date) =>
  `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;

export function matchesDate(kickoff: string | undefined, f: FixtureFilters, now: Date = new Date()): boolean {
  if (f.datePreset === "all") return true;
  // No kick-off time means we cannot place it on a date, so a date filter hides it.
  if (!kickoff) return false;
  const day = startOfDay(new Date(kickoff)).getTime();
  const today = startOfDay(now).getTime();
  switch (f.datePreset) {
    case "today":
      return day === today;
    case "tomorrow":
      return day === today + DAY_MS;
    case "week":
      return day >= today && day < today + 7 * DAY_MS;
    case "custom":
      // An empty custom date means "no date chosen yet", so nothing is hidden.
      return f.customDate === "" || toDateKey(new Date(kickoff)) === f.customDate;
  }
}

/**
 * Filter state for a fixture list. League counts are computed from the date-filtered
 * fixtures, so the numbers beside each league always match what ticking it would show.
 */
export function useFixtureFilters<T extends { league: string }>(fixtures: T[], getKickoff: (item: T) => string | undefined) {
  const [filters, setFilters] = useState<FixtureFilters>(DEFAULT_FILTERS);

  const dateFiltered = useMemo(() => fixtures.filter((m) => matchesDate(getKickoff(m), filters)), [fixtures, filters, getKickoff]);

  const leagueCounts = useMemo(() => {
    const counts = new Map<string, number>();
    // Keep every league listed (even at 0) so the list doesn't jump around.
    fixtures.forEach((m) => counts.set(m.league, counts.get(m.league) ?? 0));
    dateFiltered.forEach((m) => counts.set(m.league, (counts.get(m.league) ?? 0) + 1));
    return Array.from(counts, ([league, count]) => ({ league, count })).sort((a, b) => a.league.localeCompare(b.league));
  }, [fixtures, dateFiltered]);

  const visible = useMemo(
    () => (filters.leagues.length === 0 ? dateFiltered : dateFiltered.filter((m) => filters.leagues.includes(m.league))),
    [dateFiltered, filters.leagues],
  );

  const toggleLeague = (league: string) =>
    setFilters((f) => ({
      ...f,
      leagues: f.leagues.includes(league) ? f.leagues.filter((l) => l !== league) : [...f.leagues, league],
    }));

  const setDatePreset = (datePreset: DatePreset) => setFilters((f) => ({ ...f, datePreset }));

  /** Picking a date switches to the custom option; clearing it falls back to "all". */
  const setCustomDate = (customDate: string) =>
    setFilters((f) => ({ ...f, customDate, datePreset: customDate ? "custom" : "all" }));

  const reset = () => setFilters(DEFAULT_FILTERS);

  const activeCount = filters.leagues.length + (filters.datePreset === "all" ? 0 : 1);

  return { filters, visible, leagueCounts, activeCount, toggleLeague, setDatePreset, setCustomDate, reset };
}
