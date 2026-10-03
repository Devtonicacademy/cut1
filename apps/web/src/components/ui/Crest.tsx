"use client";

import React, { useState } from "react";

interface CrestProps {
  /** Crest URL from the fixture feed. Missing or broken URLs fall back to an initials badge. */
  src?: string | null;
  /** Club or league name: used for the fallback initials. */
  name: string;
  /** Square size in px. */
  size?: number;
  className?: string;
}

const initials = (name: string) =>
  name
    .split(/\s+/)
    .filter((w) => /[a-z0-9]/i.test(w))
    .slice(0, 2)
    .map((w) => w[0])
    .join("")
    .toUpperCase() || "?";

/**
 * A club or league crest. Decorative (`alt=""`), because the name is always printed next to it.
 * If the image is missing or fails to load, a round initials badge takes its place.
 */
export default function Crest({ src, name, size = 24, className = "" }: CrestProps) {
  const [failedSrc, setFailedSrc] = useState<string | null>(null);
  const box = { width: size, height: size };

  if (src && failedSrc !== src) {
    return (
      // eslint-disable-next-line @next/next/no-img-element
      <img
        src={src}
        alt=""
        width={size}
        height={size}
        loading="lazy"
        decoding="async"
        referrerPolicy="no-referrer"
        onError={() => setFailedSrc(src)}
        style={box}
        className={`shrink-0 object-contain ${className}`}
      />
    );
  }
  return (
    <span
      aria-hidden="true"
      style={{ ...box, fontSize: Math.max(8, Math.round(size * 0.38)) }}
      className={`flex shrink-0 items-center justify-center rounded-full border border-slate-300 bg-slate-100 font-display font-bold text-slate-600 dark:border-white/[0.12] dark:bg-slate-800 dark:text-gray-300 ${className}`}
    >
      {initials(name)}
    </span>
  );
}
