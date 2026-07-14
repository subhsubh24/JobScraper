'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { Button, Card, ErrorText } from '@/components/ui';
import { api, ApiError } from '@/lib/api';
import { useAuth } from '@/lib/auth';

// The single source of truth for the consent disclosure copy. Apple 5.1.2(i) requires the
// prompt to NAME the third-party AI and the data before the first transmission, and consent
// must be explicit (a deliberate action) and revocable (see Settings).
export const AI_PROVIDER = 'Google Gemini';
const DISCLOSURE =
  `To generate fit scores, prep packs, salary coaching and AI-coach replies, we send the ` +
  `relevant text — your resume and the job details you enter — to our AI provider ` +
  `(${AI_PROVIDER}). Nothing is sent until you turn this on, and you can turn it off anytime ` +
  `in Settings.`;

/** Whether the signed-in user has granted third-party-AI consent. */
export function hasAiConsent(user: { ai_consent?: boolean } | null): boolean {
  return user?.ai_consent === true;
}

// --------------------------------------------------------------------------- imperative flow
/**
 * Imperative consent flow for actions that live alongside other UI (e.g. the job-detail prep /
 * salary buttons). `ensureConsent()` resolves true if consent is already granted or the user
 * grants it via the modal, and false if they dismiss it — so the caller only proceeds on true.
 * Render `dialog` once in the component tree.
 */
export function useAiConsent() {
  const { user, setUser } = useAuth();
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const resolverRef = useRef<((granted: boolean) => void) | null>(null);

  const consented = hasAiConsent(user);

  function ensureConsent(): Promise<boolean> {
    if (consented) return Promise.resolve(true);
    setError(null);
    setOpen(true);
    return new Promise<boolean>((resolve) => {
      resolverRef.current = resolve;
    });
  }

  // Stable identity: the focus-trap effect in AiConsentDialog depends on `onCancel`, so an
  // inline arrow (new identity every parent render) would tear down + re-init the trap on
  // unrelated re-renders while the dialog is open — yanking focus out of the modal and back.
  // useCallback keeps it stable (settle only touches a ref + stable setState setters).
  const settle = useCallback((granted: boolean) => {
    setOpen(false);
    const resolve = resolverRef.current;
    resolverRef.current = null;
    resolve?.(granted);
  }, []);

  const handleCancel = useCallback(() => settle(false), [settle]);

  async function enable() {
    setBusy(true);
    setError(null);
    try {
      setUser(await api.grantAiConsent());
      settle(true);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Could not enable AI features. Please try again.');
    } finally {
      setBusy(false);
    }
  }

  const dialog = (
    <AiConsentDialog
      open={open}
      busy={busy}
      error={error}
      onEnable={enable}
      onCancel={handleCancel}
    />
  );

  return { consented, ensureConsent, dialog };
}

function AiConsentDialog({
  open,
  busy,
  error,
  onEnable,
  onCancel,
}: {
  open: boolean;
  busy: boolean;
  error: string | null;
  onEnable: () => void;
  onCancel: () => void;
}) {
  const dialogRef = useRef<HTMLDivElement>(null);
  // Latest-value ref so the Escape handler can honour the in-flight `busy` state WITHOUT
  // `busy` being an effect dependency (which would re-run the trap on every busy flip and
  // re-steal focus). Escape must match the visible "Not now" button, which is disabled while busy.
  const busyRef = useRef(busy);
  useEffect(() => {
    busyRef.current = busy;
  }, [busy]);

  // Accessible modal behaviour: move focus into the dialog on open, trap Tab inside it (so
  // keyboard users can't drift to the inert page behind), let Escape dismiss it, and restore
  // focus to the triggering element on close. Without this a keyboard/screen-reader user can
  // tab out of a modal that visually blocks the page — a real a11y break on the surface that
  // gates every AI feature. Deps are [open, onCancel] only (onCancel is a stable useCallback),
  // so the trap sets up/tears down on real open/close transitions, never on unrelated re-renders.
  useEffect(() => {
    if (!open) return;
    const previouslyFocused = document.activeElement as HTMLElement | null;
    const node = dialogRef.current;
    if (node && !node.contains(document.activeElement)) node.focus();

    function onKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') {
        // Don't dismiss mid-request (matches the disabled "Not now" button) — else we'd resolve
        // "declined" while the grant call is still in flight and could land afterward.
        if (busyRef.current) return;
        e.preventDefault();
        onCancel();
        return;
      }
      if (e.key !== 'Tab' || !node) return;
      const focusable = node.querySelectorAll<HTMLElement>(
        'a[href], button:not([disabled]), textarea, input, select, [tabindex]:not([tabindex="-1"])',
      );
      if (focusable.length === 0) {
        e.preventDefault();
        node.focus();
        return;
      }
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      const active = document.activeElement;
      if (e.shiftKey && (active === first || active === node)) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && active === last) {
        e.preventDefault();
        first.focus();
      }
    }

    document.addEventListener('keydown', onKeyDown);
    return () => {
      document.removeEventListener('keydown', onKeyDown);
      previouslyFocused?.focus?.();
    };
  }, [open, onCancel]);

  if (!open) return null;
  return (
    <div
      ref={dialogRef}
      tabIndex={-1}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 outline-none"
      role="dialog"
      aria-modal="true"
      aria-labelledby="ai-consent-title"
    >
      <Card className="w-full max-w-md">
        <h2 id="ai-consent-title" className="text-lg font-semibold text-slate-100">
          Enable AI features
        </h2>
        <p className="mt-3 text-sm text-slate-300">{DISCLOSURE}</p>
        {error && (
          <div className="mt-3">
            <ErrorText>{error}</ErrorText>
          </div>
        )}
        <div className="mt-5 flex gap-3">
          <Button onClick={onEnable} disabled={busy}>
            {busy ? 'Enabling…' : 'Turn on AI features'}
          </Button>
          <Button variant="secondary" onClick={onCancel} disabled={busy}>
            Not now
          </Button>
        </div>
      </Card>
    </div>
  );
}

// --------------------------------------------------------------------------- inline gate
/**
 * Inline consent gate for a surface that is ENTIRELY AI (the coach). Renders the disclosure +
 * an Enable button; calls `onEnabled` after consent is granted so the parent can proceed.
 */
export function AiConsentCard({ onEnabled }: { onEnabled?: () => void }) {
  const { setUser } = useAuth();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function enable() {
    setBusy(true);
    setError(null);
    try {
      setUser(await api.grantAiConsent());
      onEnabled?.();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Could not enable AI features. Please try again.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card className="mx-auto max-w-lg text-center">
      <h1 className="text-2xl font-extrabold">Enable AI features</h1>
      <p className="mt-2 text-slate-400">{DISCLOSURE}</p>
      {error && (
        <div className="mt-3">
          <ErrorText>{error}</ErrorText>
        </div>
      )}
      <div className="mt-5">
        <Button onClick={enable} disabled={busy}>
          {busy ? 'Enabling…' : 'Turn on AI features'}
        </Button>
      </div>
    </Card>
  );
}

// --------------------------------------------------------------------------- settings control
/** The review/revoke control (Settings). Consent must be revocable (Apple 5.1.2(i)). */
export function AiConsentSetting() {
  const { user, setUser } = useAuth();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const consented = hasAiConsent(user);

  async function toggle() {
    setBusy(true);
    setError(null);
    try {
      setUser(consented ? await api.revokeAiConsent() : await api.grantAiConsent());
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Could not update your preference. Please try again.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card>
      <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">AI features</h2>
      <p className="mt-3 text-sm text-slate-300">{DISCLOSURE}</p>
      <div className="mt-4 flex items-center justify-between gap-4">
        <span
          className={`rounded-full border px-3 py-1 text-xs font-semibold ${
            consented
              ? 'border-emerald-500/40 bg-emerald-500/10 text-emerald-300'
              : 'border-slate-600 bg-slate-800/60 text-slate-300'
          }`}
        >
          {consented ? 'Enabled' : 'Off'}
        </span>
        <Button variant={consented ? 'secondary' : 'primary'} onClick={toggle} disabled={busy}>
          {busy ? 'Saving…' : consented ? 'Turn off' : 'Turn on AI features'}
        </Button>
      </div>
      {error && (
        <div className="mt-3">
          <ErrorText>{error}</ErrorText>
        </div>
      )}
    </Card>
  );
}
