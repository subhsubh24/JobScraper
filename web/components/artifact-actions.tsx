'use client';

import { useState } from 'react';

// Copy / download affordance for a generated prep artifact (tailored résumé, cover letter,
// study plan, interview-prep pack, negotiation guide). The artifact is only useful once the
// user can get it OUT of the app — into a doc, an email, an ATS field — so every rendered
// artifact carries a Copy button (clipboard) and a Download button (a .md file). Low-emphasis
// by default so it never competes with the content, matching the sibling ReportButton.
//
// Both actions are causally honest (SIDE-EFFECT INTEGRITY): the "Copied" state is shown ONLY
// after navigator.clipboard.writeText resolves — a rejected clipboard (permission/insecure
// context) surfaces "Copy failed", never a false success. Everything runs in event handlers,
// so there is no SSR access to navigator/document.

function slugify(name: string): string {
  return (
    name
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '')
      .slice(0, 60) || 'artifact'
  );
}

export function ArtifactActions({ text, filename }: { text: string; filename: string }) {
  const [copied, setCopied] = useState(false);
  const [copyError, setCopyError] = useState(false);

  async function copy() {
    setCopyError(false);
    try {
      // The real side-effect: await the clipboard write and only then claim success.
      await navigator.clipboard.writeText(text);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopyError(true);
      window.setTimeout(() => setCopyError(false), 3000);
    }
  }

  function download() {
    // Emit the artifact as a Markdown file the way it is rendered on screen.
    const blob = new Blob([text], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${slugify(filename)}.md`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  }

  const btn =
    'inline-flex items-center gap-1 rounded text-xs text-slate-400 transition hover:text-slate-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950';

  return (
    <div className="mt-3 flex items-center gap-4">
      <button type="button" onClick={copy} className={btn}>
        {copied ? <CheckIcon /> : <CopyIcon />}
        {copied ? 'Copied' : copyError ? 'Copy failed — try again' : 'Copy'}
      </button>
      <button type="button" onClick={download} className={btn}>
        <DownloadIcon />
        Download
      </button>
      {/* Assertive announcement for screen readers when the copy completes. */}
      <span role="status" aria-live="polite" className="sr-only">
        {copied ? 'Copied to clipboard' : copyError ? 'Copy failed' : ''}
      </span>
    </div>
  );
}

function CopyIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
      <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
    </svg>
  );
}

function CheckIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M20 6 9 17l-5-5" />
    </svg>
  );
}

function DownloadIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <polyline points="7 10 12 15 17 10" />
      <line x1="12" y1="15" x2="12" y2="3" />
    </svg>
  );
}
