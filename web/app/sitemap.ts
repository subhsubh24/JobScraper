import type { MetadataRoute } from "next";

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL?.replace(/\/$/, "") || "https://careeroperator.app";

// Public, indexable routes only — never the per-user /app product or /api.
export default function sitemap(): MetadataRoute.Sitemap {
  const routes = ["", "/waitlist", "/login", "/register", "/pricing", "/privacy", "/terms"];
  return routes.map((path) => ({
    url: `${SITE_URL}${path || "/"}`,
    changeFrequency: "weekly",
    priority: path === "" ? 1 : 0.7,
  }));
}
