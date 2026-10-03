"use client";

import React, { useCallback, useEffect, useRef, useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";

export interface HeroSlide {
  id: string;
  heading: string;
  description: string;
  cta: string;
  onCta: () => void;
  /** Tailwind-free CSS gradient layers, drawn bottom to top. */
  background: string;
}

interface HeroCarouselProps {
  slides: HeroSlide[];
  /** Milliseconds between automatic slide changes. */
  interval?: number;
}

const FADE_MS = 700;

/** Faint pitch markings so the gradients read as "football" without any external image. */
function PitchLines() {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 800 400"
      preserveAspectRatio="xMidYMid slice"
      className="absolute inset-0 h-full w-full text-white/[0.09]"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
    >
      <rect x="20" y="20" width="760" height="360" rx="6" />
      <line x1="400" y1="20" x2="400" y2="380" />
      <circle cx="400" cy="200" r="58" />
      <circle cx="400" cy="200" r="3" fill="currentColor" />
      <rect x="20" y="115" width="120" height="170" />
      <rect x="660" y="115" width="120" height="170" />
    </svg>
  );
}

export default function HeroCarousel({ slides, interval = 6000 }: HeroCarouselProps) {
  const [active, setActive] = useState(0);
  // The slide that just faded out keeps its zoom until its fade ends, so it does not snap back to scale(1).
  const [leaving, setLeaving] = useState<number | null>(null);
  const [paused, setPaused] = useState(false);
  const leaveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const count = slides.length;

  const activeRef = useRef(0);
  const goTo = useCallback(
    (next: number) => {
      const target = (next + count) % count;
      const prev = activeRef.current;
      if (target === prev) return;
      activeRef.current = target;
      setLeaving(prev);
      setActive(target);
      if (leaveTimer.current) clearTimeout(leaveTimer.current);
      leaveTimer.current = setTimeout(() => setLeaving(null), FADE_MS);
    },
    [count],
  );

  useEffect(() => () => {
    if (leaveTimer.current) clearTimeout(leaveTimer.current);
  }, []);

  // Autoplay, paused while the user hovers or focuses the carousel, and off for reduced-motion users.
  useEffect(() => {
    if (paused || count < 2) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const t = setInterval(() => goTo(active + 1), interval);
    return () => clearInterval(t);
  }, [active, paused, count, interval, goTo]);

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowLeft") goTo(active - 1);
    if (e.key === "ArrowRight") goTo(active + 1);
  };

  const arrow =
    "absolute top-1/2 z-20 -translate-y-1/2 rounded-full border border-white/20 bg-black/30 p-2 text-white backdrop-blur-sm transition-colors hover:bg-black/50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-emerald-400";

  return (
    <section
      aria-roledescription="carousel"
      aria-label="Why LivelyBorg AI"
      tabIndex={0}
      onKeyDown={onKeyDown}
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
      onFocus={() => setPaused(true)}
      onBlur={() => setPaused(false)}
      className="relative h-64 overflow-hidden rounded-panel border border-slate-200 bg-[#0B0F19] shadow-sm dark:border-glass sm:h-72 lg:h-80"
    >
      {slides.map((s, i) => {
        const isActive = i === active;
        const zoom = isActive || i === leaving;
        return (
          <div
            key={s.id}
            role="group"
            aria-roledescription="slide"
            aria-label={`${i + 1} of ${count}`}
            aria-hidden={!isActive}
            style={{ transitionDuration: `${FADE_MS}ms` }}
            // Opacity only: the wrapper never has a transform, so it cannot collide with the zoom or the copy.
            className={`absolute inset-0 transition-opacity ease-in-out ${isActive ? "z-10 opacity-100" : "pointer-events-none opacity-0"}`}
          >
            <div
              className={`absolute inset-0 ${zoom ? "hero-kenburns" : ""}`}
              style={{ background: s.background }}
            >
              <PitchLines />
            </div>
            <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-black/10 to-transparent" />

            {/* Re-keyed on activation so the entrance animation replays each time the slide returns. */}
            <div key={isActive ? "in" : "out"} className={`relative flex h-full max-w-2xl flex-col justify-end gap-3 px-14 py-6 sm:px-16 sm:py-8 lg:px-20 lg:py-10 ${isActive ? "hero-copy-in" : ""}`}>
              <h2 className="font-display text-2xl font-bold leading-tight tracking-tight text-white sm:text-3xl lg:text-4xl">{s.heading}</h2>
              <p className="text-sm leading-relaxed text-slate-200 sm:text-base">{s.description}</p>
              <div>
                <button
                  onClick={s.onCta}
                  tabIndex={isActive ? 0 : -1}
                  className="rounded-lg bg-emerald-500 px-4 py-2.5 text-sm font-bold text-black shadow-glow-emerald transition-colors hover:bg-emerald-400"
                >
                  {s.cta}
                </button>
              </div>
            </div>
          </div>
        );
      })}

      <button onClick={() => goTo(active - 1)} aria-label="Previous slide" className={`${arrow} left-3`}>
        <ChevronLeft className="h-5 w-5" />
      </button>
      <button onClick={() => goTo(active + 1)} aria-label="Next slide" className={`${arrow} right-3`}>
        <ChevronRight className="h-5 w-5" />
      </button>

      <div className="absolute bottom-3 right-4 z-20 flex gap-1.5 sm:bottom-4 sm:right-6">
        {slides.map((s, i) => (
          <button
            key={s.id}
            onClick={() => goTo(i)}
            aria-label={`Go to slide ${i + 1}`}
            aria-current={i === active}
            className={`h-2 rounded-full transition-all ${i === active ? "w-6 bg-emerald-400" : "w-2 bg-white/40 hover:bg-white/70"}`}
          />
        ))}
      </div>
    </section>
  );
}
