import React from "react";

interface GlassCardProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Highlights the card with the emerald glow (selected / predictive focus). */
  active?: boolean;
}

/** Surface level 1: blurred charcoal glass with a 1px hairline border, 16px radius. */
export default function GlassCard({ active = false, className = "", ...props }: GlassCardProps) {
  return (
    <div
      {...props}
      className={`overflow-hidden rounded-panel border transition-all duration-200 ${
        active
          ? "border-emerald-500 bg-emerald-50/70 shadow-md ring-1 ring-emerald-500/30 dark:bg-slate-800/80 dark:shadow-glow-emerald"
          : "border-slate-200 bg-white shadow-sm hover:border-slate-300 dark:border-glass dark:bg-surface-glass dark:shadow-none dark:backdrop-blur-glass dark:hover:border-white/[0.16]"
      } ${className}`}
    />
  );
}
