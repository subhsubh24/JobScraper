import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/lib/auth";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL?.replace(/\/$/, "");
const DESCRIPTION =
  "AI-powered job search: fit scoring against your resume, role-specific interview prep, an AI career coach, and a pipeline CRM — so you spend your energy on the roles that actually fit.";

export const metadata: Metadata = {
  // Only set metadataBase when a real site URL is configured, so relative OG/canonical
  // URLs resolve in production without hard-coding a guessed domain in the repo.
  ...(SITE_URL ? { metadataBase: new URL(SITE_URL) } : {}),
  title: {
    default: "Career Operator — Run your job search like an operator",
    template: "%s · Career Operator",
  },
  description: DESCRIPTION,
  applicationName: "Career Operator",
  keywords: [
    "job search",
    "interview prep",
    "AI career coach",
    "resume fit score",
    "job application tracker",
    "pipeline CRM",
  ],
  openGraph: {
    type: "website",
    siteName: "Career Operator",
    title: "Career Operator — Run your job search like an operator",
    description: DESCRIPTION,
    ...(SITE_URL ? { url: SITE_URL } : {}),
  },
  twitter: {
    card: "summary_large_image",
    title: "Career Operator — Run your job search like an operator",
    description: DESCRIPTION,
  },
  // The signed-in product lives under /app and the API under /api — neither should be
  // indexed. robots.ts enforces this; this is the page-level signal.
  robots: { index: true, follow: true },
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-[#0b1020] text-slate-100">
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
