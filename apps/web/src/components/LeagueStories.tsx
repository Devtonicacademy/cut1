"use client";

import React from "react";

interface LeagueStoriesProps {
  leagues: { league: string; count: number }[];
  selected: string[];
  onToggle: (league: string) => void;
}

const initials = (name: string) =>
  name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0])
    .join("")
    .toUpperCase();

/** Instagram-style "stories" row: a swipeable strip of round league avatars that toggle the league filter. */
export default function LeagueStories({ leagues, selected, onToggle }: LeagueStoriesProps) {
  if (leagues.length === 0) return null;
  return (
    <div
      role="group"
      aria-label="Leagues"
      className="-mx-3.5 flex gap-3.5 overflow-x-auto px-3.5 pb-1 no-scrollbar sm:mx-0 sm:px-0"
    >
      {leagues.map(({ league, count }) => {
        const on = selected.includes(league);
        return (
          <button
            key={league}
            onClick={() => onToggle(league)}
            aria-pressed={on}
            className={`flex w-16 shrink-0 flex-col items-center gap-1 ${count === 0 && !on ? "opacity-40" : ""}`}
          >
            <span
              className={`relative flex h-14 w-14 items-center justify-center rounded-full p-[3px] transition-colors ${
                on ? "bg-emerald-500" : "bg-gradient-to-tr from-emerald-500/70 to-amber-500/70"
              }`}
            >
              <span className="flex h-full w-full items-center justify-center rounded-full border-2 border-slate-50 bg-white font-display text-sm font-bold text-slate-800 dark:border-[#0B0F19] dark:bg-slate-800 dark:text-white">
                {initials(league)}
              </span>
              <span className="absolute -bottom-0.5 -right-0.5 rounded-full border-2 border-slate-50 bg-emerald-500 px-1 font-mono text-[9px] font-semibold leading-4 text-black dark:border-[#0B0F19]">
                {count}
              </span>
            </span>
            <span className="w-full truncate text-center text-[10px] text-slate-600 dark:text-gray-300">{league}</span>
          </button>
        );
      })}
    </div>
  );
}
