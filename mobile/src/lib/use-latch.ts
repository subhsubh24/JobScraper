import { useMemo, useRef } from 'react';

export interface Latch {
  /** Acquire the latch. Returns true for the first caller, false while an op is in flight. */
  enter: () => boolean;
  /** Release the latch. Call in `finally` so it clears on success, error, and early return. */
  leave: () => void;
}

/**
 * A synchronous single-flight re-entry latch for async action handlers that fire a paid or
 * otherwise-expensive request (an LLM generation, a scrape, a metered API call).
 *
 * A `useState` "busy" flag CANNOT guard a same-tick double-fire: a fast double-tap delivers two
 * onPress calls that both close over the pre-render `busy=false`, and a control's `disabled` prop
 * only takes effect after the re-render propagates — on React Native that crosses the bridge,
 * measurably later than two quick taps. A ref flips synchronously and is shared across those stale
 * closures, so the second call short-circuits before it fires a duplicate request (which would burn
 * a second server-side spend-ceiling slot and desync the shown result from the persisted one).
 *
 * The returned object is stable across renders (methods close over a single ref), so it is safe to
 * list in a `useCallback`/`useEffect` dependency array without churning the memoization. Correctness
 * depends only on the ref, never on this object's identity.
 *
 * Usage:
 *   const latch = useLatch();
 *   async function submit() {
 *     if (!latch.enter()) return;      // second same-tick tap bails here
 *     try {
 *       await api.somePaidCall();
 *     } finally {
 *       latch.leave();                 // always release, on every exit path
 *     }
 *   }
 */
export function useLatch(): Latch {
  const busy = useRef(false);
  return useMemo<Latch>(
    () => ({
      enter() {
        if (busy.current) return false;
        busy.current = true;
        return true;
      },
      leave() {
        busy.current = false;
      },
    }),
    [],
  );
}
