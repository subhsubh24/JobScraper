import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// Pre-launch SITE GATE: when SITE_GATE_PASSWORD is set, the deployed app is
// password-protected (HTTP Basic) so we never expose a half-baked product — EXCEPT the
// public marketing + legal routes below, so people can still land and join the waitlist.
// Unset SITE_GATE_PASSWORD at launch (every ship-critical QUALITY_SCORECARD dim A/A+ +
// readiness) to open the app. The password VALUE is human-applied (never committed).
//
// NOTE: this gates the Next.js web app only. The FastAPI API (/api/*) is a separate
// Vercel service with its own JWT auth; the mobile app is gated pre-launch via
// TestFlight / an internal track. Exempt routes are the marketing surfaces.
const EXEMPT_EXACT = new Set(['/']); // landing / "coming soon" is public
const EXEMPT_PREFIXES = ['/coming-soon', '/waitlist', '/privacy', '/terms', '/legal'];

function isExempt(pathname: string): boolean {
  if (EXEMPT_EXACT.has(pathname)) return true;
  return EXEMPT_PREFIXES.some((p) => pathname === p || pathname.startsWith(p + '/'));
}

export function middleware(req: NextRequest) {
  const password = process.env.SITE_GATE_PASSWORD;
  if (!password) return NextResponse.next(); // gate OFF -> launched / fully open

  if (isExempt(req.nextUrl.pathname)) return NextResponse.next();

  const header = req.headers.get('authorization') ?? '';
  if (header.startsWith('Basic ')) {
    try {
      const supplied = atob(header.slice(6)).split(':')[1] ?? '';
      if (supplied === password) return NextResponse.next();
    } catch {
      /* malformed header -> fall through to 401 */
    }
  }
  return new NextResponse('Authentication required', {
    status: 401,
    headers: { 'WWW-Authenticate': 'Basic realm="Career Operator (pre-launch)"' },
  });
}

export const config = {
  // Run on all routes except the API (separate service), Next internals, and static files.
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico|.*\\..*).*)'],
};
