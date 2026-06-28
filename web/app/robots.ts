import type { MetadataRoute } from "next";

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL?.replace(/\/$/, "") || "https://careeroperator.app";

// Marketing + legal pages are indexable; the signed-in product (/app) and the API
// (/api) are not — they're per-user and behind auth, so they have no business in search.
export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: "/",
      disallow: ["/app", "/api"],
    },
    sitemap: `${SITE_URL}/sitemap.xml`,
  };
}
