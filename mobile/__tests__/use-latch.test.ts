/// <reference types="jest" />
// The latch must be SYNCHRONOUS: the second enter() in the same tick (before any re-render or
// leave()) must fail, which is exactly what a same-tick double-tap needs and what a useState flag
// cannot provide. Rendered via a host hook-runner so useRef is real.
import { renderHook } from '@testing-library/react-native';
import { useLatch } from '@/lib/use-latch';

it('enter() succeeds once, then fails synchronously until leave()', () => {
  const { result } = renderHook(() => useLatch());
  // Same-tick: first tap acquires, second tap (before leave) is rejected — no re-render between.
  expect(result.current.enter()).toBe(true);
  expect(result.current.enter()).toBe(false);
  expect(result.current.enter()).toBe(false);
  // Release, then it can be acquired again (next user action).
  result.current.leave();
  expect(result.current.enter()).toBe(true);
});

it('leave() is idempotent and safe to call when not held', () => {
  const { result } = renderHook(() => useLatch());
  result.current.leave();
  expect(result.current.enter()).toBe(true);
  result.current.leave();
  result.current.leave();
  expect(result.current.enter()).toBe(true);
});
