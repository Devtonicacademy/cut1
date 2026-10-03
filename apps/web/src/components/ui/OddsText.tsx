import React from "react";

interface OddsTextProps extends React.HTMLAttributes<HTMLSpanElement> {
  value: number;
  /** Decimal places: 2 for odds, 0 for percentages. */
  digits?: number;
  prefix?: string;
  suffix?: string;
}

/** Numbers that must line up in tables (odds, probabilities, EV) in JetBrains Mono. */
export default function OddsText({ value, digits = 2, prefix = "", suffix = "", className = "", ...props }: OddsTextProps) {
  return (
    <span {...props} className={`font-mono tabular-nums ${className}`}>
      {prefix}
      {value.toFixed(digits)}
      {suffix}
    </span>
  );
}
