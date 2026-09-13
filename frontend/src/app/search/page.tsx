// Search results page. Server Component by default (SSR — frontend/CLAUDE.md
// "ALWAYS SSR restaurant listing pages and search pages"). Visual design is
// deliberately deferred — see app/page.tsx's note; this is route scaffolding
// only.
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Search Results",
};

export default function SearchPage() {
  return (
    <main>
      <h1>Search Results</h1>
      <p>Under construction — search results UI is pending the homepage/search visual design decision.</p>
    </main>
  );
}
