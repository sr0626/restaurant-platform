// Native Next.js 14 App Router robots.txt — served automatically at
// /robots.txt, no separate route handler needed (frontend/CLAUDE.md "SEO
// Requirements": "robots.txt allows all crawlers"). Disallows only the
// auth-gated/non-public route trees (owner/manager portal, admin panel,
// login, claim submission) — everything public (home, search, restaurant
// detail pages) stays crawlable.
import type { MetadataRoute } from "next";
import { SITE_URL } from "@/lib/site";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: "/",
      disallow: ["/portal", "/admin", "/login", "/claim"],
    },
    sitemap: `${SITE_URL}/sitemap.xml`,
  };
}
