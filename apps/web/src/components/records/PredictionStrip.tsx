import React from "react";
import OddsText from "@/components/ui/OddsText";

interface PredictionStripProps {
  p_home: number;
  p_draw: number;
  p_away: number;
  /** The model's pick, highlighted in emerald. */
  pick: "1" | "X" | "2";
  /** What actually happened, ringed in amber (past matches only). */
  actual?: "1" | "X" | "2" | null;
}

/** The three outcome probabilities side by side: Home | Draw | Away. */
export default function PredictionStrip({ p_home, p_draw, p_away, pick, actual }: PredictionStripProps) {
  const cells = [
    { key: "1", label: "Home", value: p_home },
    { key: "X", label: "Draw", value: p_draw },
    { key: "2", label: "Away", value: p_away },
  ] as const;
  return (
    <div className="grid grid-cols-3 gap-1.5 text-center font-mono text-xs">
      {cells.map((c) => (
        <div
          key={c.key}
          className={`rounded-lg border px-1 py-1 ${
            c.key === pick
              ? "border-emerald-500/40 bg-emerald-500/[0.12] font-bold text-emerald-600 dark:text-emerald-400"
              : "border-slate-200 text-slate-500 dark:border-white/[0.08] dark:text-gray-400"
          } ${actual === c.key ? "ring-1 ring-amber-400" : ""}`}
        >
          <div className="text-[9px] uppercase opacity-80">{c.label}</div>
          <OddsText value={c.value * 100} digits={0} suffix="%" />
        </div>
      ))}
    </div>
  );
}
