// Native Next.js 14 App Router sitemap — served automatically at
// /sitemap.xml, no separate route handler needed (frontend/CLAUDE.md "SEO
// Requirements": "sitemap.xml generated at build time from all active
// locations").
//
// Restaurant detail URLs are built from the real, public GET /search
// endpoint (docs/API_CONTRACTS.md "GET /search") — the same typed client
// function the search results page already uses — not a hardcoded or
// fabricated URL list. There is no unauthenticated "list every restaurant"
// endpoint (GET /restaurants requires owner-or-admin auth), so this walks
// /search's brand-level results at its maximum radius (100mi, the
// server-enforced ceiling — see backend/app/routers/search.py's
// `Query(..., le=100)`) around its DFW-center default (no lat/lng passed),
// which is the right tool for "every real public restaurant" on a
// single-metro Phase 1 directory (root CLAUDE.md "Current Phase": DFW).
import type { MetadataRoute } from "next";
import { searchRestaurants } from "@/lib/api/search";
import { SITE_URL } from "@/lib/site";

const SEARCH_PAGE_SIZE = 100;
/** Server-enforced ceiling on GET /search's `radius` query param. */
const MAX_SEARCH_RADIUS_MILES = 100;
/** Hard stop so a backend bug (e.g. `total` never shrinking) can't turn
 * this into an unbounded loop against a public endpoint. Comfortably above
 * any realistic Phase 1 DFW restaurant count (docs/DECISIONS.md "Data
 * seeding": ~500 seeded restaurants). */
const MAX_PAGES = 50;

async function fetchAllPublicSlugs(): Promise<string[]> {
  const slugs = new Set<string>();

  for (let page = 1; page <= MAX_PAGES; page += 1) {
    const result = await searchRestaurants({
      radius: MAX_SEARCH_RADIUS_MILES,
      page,
      page_size: SEARCH_PAGE_SIZE,
    });
    for (const item of result.results) {
      slugs.add(item.slug);
    }
    if (result.results.length < SEARCH_PAGE_SIZE || slugs.size >= result.total) {
      break;
    }
  }

  return [...slugs];
}

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const entries: MetadataRoute.Sitemap = [
    {
      url: SITE_URL,
      lastModified: new Date(),
      changeFrequency: "daily",
      priority: 1,
    },
  ];

  try {
    const slugs = await fetchAllPublicSlugs();
    for (const slug of slugs) {
      entries.push({
        url: `${SITE_URL}/restaurant/${slug}`,
        lastModified: new Date(),
        changeFrequency: "weekly",
        priority: 0.8,
      });
    }
  } catch {
    // Backend unreachable at build/request time — still serve a valid
    // sitemap with just the homepage rather than failing the whole route
    // (frontend/CLAUDE.md "ALWAYS handle API errors gracefully").
  }

  return entries;
}
