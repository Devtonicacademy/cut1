import { useCallback, useEffect, useRef, useState } from "react";
import { apiJson } from "@/lib/auth";
import { TrackMatches } from "@/types";

const LIVE_REFRESH_MS = 30_000; // while a match is on
const IDLE_REFRESH_MS = 5 * 60_000;

/**
 * Loads past and ongoing matches and keeps them fresh: every 30 seconds while a match is in play, every
 * 5 minutes otherwise, and not at all while the tab is hidden (it catches up the moment it is shown again).
 */
export function useTrackMatches() {
  const [data, setData] = useState<TrackMatches | null>(null);
  const [failed, setFailed] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const hasOngoing = useRef(false);

  const load = useCallback(async () => {
    const res = await apiJson<TrackMatches>("/track-record/matches?limit=300");
    if (res.data) {
      hasOngoing.current = res.data.ongoing.length > 0;
      setData(res.data);
      setFailed(false);
    } else {
      setFailed(true);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    const tick = async () => {
      if (document.visibilityState === "visible") await load();
      if (!cancelled) timer.current = setTimeout(tick, hasOngoing.current ? LIVE_REFRESH_MS : IDLE_REFRESH_MS);
    };
    const onVisible = () => {
      if (document.visibilityState === "visible") {
        if (timer.current) clearTimeout(timer.current);
        tick();
      }
    };
    tick();
    document.addEventListener("visibilitychange", onVisible);
    return () => {
      cancelled = true;
      if (timer.current) clearTimeout(timer.current);
      document.removeEventListener("visibilitychange", onVisible);
    };
  }, [load]);

  return { data, failed, reload: load };
}
