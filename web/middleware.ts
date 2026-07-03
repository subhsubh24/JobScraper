import { NextResponse } from 'next/server';

// SITE GATE removed 2026-07-02 (owner request): the app is PUBLIC. This middleware is now a
// pass-through — SITE_GATE_PASSWORD is no longer honored, so /login, /register, /app etc. are
// reachable directly (no browser Basic-Auth popup). To re-enable a pre-launch gate, restore the
// HTTP Basic Auth check against process.env.SITE_GATE_PASSWORD here (and keep marketing/legal
// routes exempt). See git history for the previous implementation.
export function middleware() {
  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico|.*\\..*).*)'],
};
