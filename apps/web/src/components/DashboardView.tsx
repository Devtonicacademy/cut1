"use client";

import React from "react";
import { BookmarkMinus, CheckCircle2, Clock, Trophy, XCircle } from "lucide-react";
import { useAuth } from "@/lib/auth";
import { SavedFixture } from "@/types";
import Crest from "@/components/ui/Crest";
import GlassCard from "@/components/ui/GlassCard";
import Chip from "@/components/ui/Chip";
import OddsText from "@/components/ui/OddsText";
import Reveal, { staggerDelay } from "@/components/motion/Reveal";

const when = (iso: string | null) =>
  iso ? new Date(iso).toLocaleString(undefined, { weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit", hour12: false }) : "Time to be confirmed";

function SavedCard({ item, onRemove }: { item: SavedFixture; onRemove: () => void }) {
  const probs = [
    { key: "1", label: "Home", value: item.p_home },
    { key: "X", label: "Draw", value: item.p_draw },
    { key: "2", label: "Away", value: item.p_away },
  ];
  return (
    <GlassCard className="flex h-full flex-col">
      <div className="flex flex-1 flex-col gap-4 p-4">
        <div className="flex items-center justify-between gap-2">
          <Chip tone="success" className="max-w-[60%] truncate uppercase tracking-wider">{item.league}</Chip>
          {item.status === "finished" ? (
            <Chip tone={item.pick_correct ? "success" : "caution"} pill>
              {item.pick_correct ? <CheckCircle2 className="h-3 w-3" /> : <XCircle className="h-3 w-3" />}
              {item.pick_correct ? "Model right" : "Model wrong"}
            </Chip>
          ) : (
            <Chip tone="info" pill>
              <Clock className="h-3 w-3" />
              {item.status === "awaiting_result" ? "Awaiting result" : "Upcoming"}
            </Chip>
          )}
        </div>

        <div className="grid grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] items-start gap-2">
          {[{ name: item.home_team, crest: item.home_crest }, null, { name: item.away_team, crest: item.away_crest }].map((side, i) =>
            side ? (
              <div key={i} className="flex min-w-0 flex-col items-center gap-1.5 text-center">
                <Crest src={side.crest} name={side.name} size={40} />
                <span className="line-clamp-2 [overflow-wrap:anywhere] font-display text-sm font-semibold leading-tight text-slate-900 dark:text-white">{side.name}</span>
              </div>
            ) : (
              <div key={i} className="flex flex-col items-center gap-1 pt-1 text-center">
                {item.status === "finished" ? (
                  <span className="font-mono text-2xl font-bold text-slate-900 dark:text-white">{item.home_goals} - {item.away_goals}</span>
                ) : (
                  <span className="max-w-[7rem] font-mono text-[11px] text-slate-600 dark:text-gray-300">{when(item.kickoff_utc)}</span>
                )}
                <span className="rounded-full border border-slate-200 px-2 py-0.5 text-[10px] font-black text-slate-500 dark:border-white/[0.12] dark:text-gray-400">
                  {item.status === "finished" ? "FT" : "VS"}
                </span>
              </div>
            ),
          )}
        </div>

        <div>
          <p className="mb-1 text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-gray-400">
            {item.status === "finished" ? "Prediction locked before kickoff" : "Model prediction"}
          </p>
          <div className="grid grid-cols-3 gap-1.5 text-center font-mono text-xs">
            {probs.map((p) => (
              <div
                key={p.key}
                className={`rounded-lg border px-1 py-1.5 ${
                  p.key === item.pick
                    ? "border-emerald-500/40 bg-emerald-500/[0.12] font-bold text-emerald-600 dark:text-emerald-400"
                    : "border-slate-200 text-slate-500 dark:border-white/[0.08] dark:text-gray-400"
                } ${item.status === "finished" && p.key === item.actual ? "ring-1 ring-amber-400" : ""}`}
              >
                <div className="text-[10px] opacity-80">{p.label}</div>
                <OddsText value={p.value * 100} digits={0} suffix="%" />
              </div>
            ))}
          </div>
          {item.status === "finished" && <p className="mt-1 text-[10px] text-slate-500 dark:text-gray-400">Amber ring: what actually happened.</p>}
        </div>

        <button
          onClick={onRemove}
          className="mt-auto flex items-center justify-center gap-1.5 rounded-lg border border-slate-200 py-1.5 text-[11px] font-bold text-slate-600 transition-colors hover:bg-slate-100 dark:border-white/[0.08] dark:text-gray-300 dark:hover:bg-slate-800"
        >
          <BookmarkMinus className="h-3.5 w-3.5" /> Remove
        </button>
      </div>
    </GlassCard>
  );
}

/** The signed-in user's saved fixtures, with the model's prediction and (once played) the result. */
export default function DashboardView({ onBrowse }: { onBrowse: () => void }) {
  const { ready, user, saved, toggleSave, openSignIn } = useAuth();

  if (ready && !user) {
    return (
      <div className="mx-auto max-w-md py-16 text-center">
        <Trophy className="mx-auto mb-3 h-8 w-8 text-emerald-500" />
        <h2 className="font-display text-lg font-semibold text-slate-900 dark:text-white">Your personal dashboard</h2>
        <p className="mb-4 mt-1 text-sm text-slate-600 dark:text-gray-400">Sign in to keep the matches you follow in one place.</p>
        <button onClick={openSignIn} className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-bold text-black hover:bg-emerald-400">Sign in</button>
      </div>
    );
  }

  const finished = saved.filter((s) => s.status === "finished");
  const right = finished.filter((s) => s.pick_correct).length;

  return (
    <div className="mx-auto max-w-6xl space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-2">
        <div>
          <h2 className="font-display text-xl font-bold text-slate-900 dark:text-white">My dashboard</h2>
          <p className="text-xs text-slate-600 dark:text-gray-400">
            {user ? `Saved by ${user.name || user.email}` : ""}
            {finished.length > 0 && ` · the model was right on ${right} of ${finished.length} finished match${finished.length === 1 ? "" : "es"}`}
          </p>
        </div>
        <Chip tone="neutral">{saved.length} saved</Chip>
      </div>

      {saved.length === 0 ? (
        <div className="rounded-panel border border-dashed border-slate-300 p-10 text-center dark:border-white/[0.12]">
          <p className="text-sm text-slate-600 dark:text-gray-300">Nothing saved yet. Tap the bookmark on any match to add it here.</p>
          <button onClick={onBrowse} className="mt-3 rounded-lg bg-emerald-500 px-4 py-2 text-sm font-bold text-black hover:bg-emerald-400">Browse matches</button>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {saved.map((item, i) => (
            <Reveal key={item.fixture_id} delay={staggerDelay(i % 3)}>
              <SavedCard item={item} onRemove={() => toggleSave(item.fixture_id)} />
            </Reveal>
          ))}
        </div>
      )}
    </div>
  );
}
