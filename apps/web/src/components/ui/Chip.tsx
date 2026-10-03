import React from "react";

export type ChipTone = "success" | "caution" | "info" | "neutral";

const TONES: Record<ChipTone, string> = {
  success: "bg-emerald-100 text-emerald-800 border-emerald-300 dark:bg-emerald-500/[0.12] dark:text-emerald-500 dark:border-emerald-500/30",
  caution: "bg-amber-100 text-amber-800 border-amber-300 dark:bg-amber-500/[0.12] dark:text-amber-500 dark:border-amber-500/30",
  info: "bg-blue-100 text-blue-800 border-blue-300 dark:bg-blue-500/[0.12] dark:text-blue-400 dark:border-blue-500/30",
  neutral: "bg-slate-100 text-slate-600 border-slate-200 dark:bg-white/[0.04] dark:text-gray-400 dark:border-white/[0.08]",
};

interface ChipProps extends React.HTMLAttributes<HTMLSpanElement> {
  tone?: ChipTone;
  /** Pills are for live status ("LIVE 74'", "AI CONFIDENCE 84%"); chips use 6px radius. */
  pill?: boolean;
}

/** Prediction badge / stat chip in JetBrains Mono, per the design system. */
export default function Chip({ tone = "neutral", pill = false, className = "", ...props }: ChipProps) {
  return (
    <span
      {...props}
      className={`inline-flex items-center gap-1 border px-2 py-0.5 font-mono text-[10px] font-semibold ${
        pill ? "rounded-full" : "rounded-chip"
      } ${TONES[tone]} ${className}`}
    />
  );
}
