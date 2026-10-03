"use client";

import React from "react";
import { m, useScroll, useSpring } from "framer-motion";

/** Thin emerald bar at the top of the page that fills as the visitor scrolls. */
export default function ScrollProgress() {
  const { scrollYProgress } = useScroll();
  const scaleX = useSpring(scrollYProgress, { stiffness: 140, damping: 24, restDelta: 0.001 });
  return (
    <m.div
      aria-hidden="true"
      data-testid="scroll-progress"
      style={{ scaleX, transformOrigin: "0% 50%" }}
      className="pointer-events-none fixed inset-x-0 top-0 z-[70] h-0.5 bg-emerald-400"
    />
  );
}
