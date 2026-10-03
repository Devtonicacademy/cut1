"use client";

import React from "react";
import { m } from "framer-motion";

interface RevealProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Seconds to wait before the reveal starts (used for staggering siblings). */
  delay?: number;
  /** Distance in px the element rises from. */
  y?: number;
}

/**
 * Fades and lifts its children into place the first time they scroll into view.
 * Only this wrapper is transformed, so children keep full control of their own transforms.
 * Needs a <LazyMotion> ancestor; reduced-motion users are handled by the page's <MotionConfig>.
 */
export default function Reveal({ delay = 0, y = 24, children, ...rest }: RevealProps) {
  return (
    <m.div
      initial={{ opacity: 0, y }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-60px" }}
      transition={{ duration: 0.55, ease: [0.22, 1, 0.36, 1], delay }}
      {...(rest as object)}
    >
      {children}
    </m.div>
  );
}

/** Stagger delay for the nth item in a list, capped so a long list never makes people wait. */
export const staggerDelay = (index: number, step = 0.06, max = 0.36) => Math.min(index * step, max);
