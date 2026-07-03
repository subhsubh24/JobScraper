'use client';

import { useEffect, useRef } from 'react';

// Cloudflare Turnstile widget for the public forms (bot/abuse protection — Track F).
//
// The public site key is a build-time NEXT_PUBLIC_ var (safe to expose in the client bundle).
// When it is UNSET the widget renders nothing and `captchaConfigured` is false, so forms treat
// captcha as not-required — matching the SERVER, which only enforces once TURNSTILE_SECRET is
// set. So pre-launch (neither key set) nothing changes for the user; the seam is inert.
const SITE_KEY = process.env.NEXT_PUBLIC_TURNSTILE_SITEKEY;

/** True only when the owner has connected Turnstile on the web client. */
export const captchaConfigured: boolean = Boolean(SITE_KEY);

// Minimal typing for the global the Cloudflare script injects (explicit-render API).
interface TurnstileApi {
  render: (
    el: HTMLElement,
    opts: {
      sitekey: string;
      callback: (token: string) => void;
      'error-callback'?: () => void;
      'expired-callback'?: () => void;
      theme?: 'auto' | 'light' | 'dark';
    },
  ) => string;
  remove: (widgetId: string) => void;
}

declare global {
  // `var` is required here: ambient global augmentation of `globalThis` (let/const don't
  // attach to the global type). ESLint's no-var is not triggered inside `declare global`.
  var turnstile: TurnstileApi | undefined;
}

const SCRIPT_SRC = 'https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit';

// Load the Turnstile script exactly once, resolving when `window.turnstile` is ready.
function ensureScript(): Promise<void> {
  return new Promise((resolve) => {
    if (typeof window === 'undefined') return; // never reached: effects run client-side only
    if (window.turnstile) {
      resolve();
      return;
    }
    const existing = document.querySelector<HTMLScriptElement>('script[data-turnstile]');
    if (existing) {
      existing.addEventListener('load', () => resolve(), { once: true });
      return;
    }
    const script = document.createElement('script');
    script.src = SCRIPT_SRC;
    script.async = true;
    script.defer = true;
    script.dataset.turnstile = 'true';
    script.addEventListener('load', () => resolve(), { once: true });
    document.head.appendChild(script);
  });
}

/**
 * Renders the Turnstile challenge and reports the solved token (or null on error/expiry) via
 * `onToken`. Renders nothing when the site key is unset — the caller should NOT require a token
 * in that case (`captchaConfigured` is the signal).
 */
export function Turnstile({ onToken }: { onToken: (token: string | null) => void }) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const widgetIdRef = useRef<string | null>(null);

  useEffect(() => {
    if (!SITE_KEY) return;
    const siteKey: string = SITE_KEY; // narrowed to a definite string for the closure below
    let cancelled = false;
    void ensureScript().then(() => {
      if (cancelled || !containerRef.current || !window.turnstile) return;
      if (widgetIdRef.current) return; // guard against a double render (strict-mode remount)
      widgetIdRef.current = window.turnstile.render(containerRef.current, {
        sitekey: siteKey,
        callback: (token: string) => onToken(token),
        'error-callback': () => onToken(null),
        'expired-callback': () => onToken(null),
        theme: 'auto',
      });
    });
    return () => {
      cancelled = true;
      const id = widgetIdRef.current;
      if (id && window.turnstile) {
        try {
          window.turnstile.remove(id);
        } catch {
          // widget already gone — nothing to clean up
        }
        widgetIdRef.current = null;
      }
    };
    // Bind onToken once at mount; the parent passes a stable setState updater.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (!SITE_KEY) return null;
  return <div ref={containerRef} className="mt-1" />;
}
