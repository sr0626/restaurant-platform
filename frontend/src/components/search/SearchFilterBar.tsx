"use client";

// Search results page filter bar — same visual form as the homepage
// Hero's search bar (location + cuisine/dish/restaurant text, "Spice
// Market" tokens) but wired to actually drive this page's results instead
// of just navigating to it.
//
// FLAGGED GAP (see PR description): `docs/API_CONTRACTS.md`'s `GET
// /search` only documents `lat`/`lng`/`radius`/`cuisine[]`/`dietary[]`/
// `type[]`/`page`/`page_size` — there is no free-text search param and no
// "resolve this city/ZIP to lat/lng" endpoint in Phase 1. So `location`
// and `q` below are read from the URL (completing Hero.tsx's navigation
// contract — the fields round-trip and stay visible) and kept in local
// state so the inputs work, but they are deliberately NOT sent to
// `searchRestaurants()` in `SearchResults` — there is nothing real to send
// them as. Only `cuisine` (which Hero already puts on the URL and which
// maps directly to the real `cuisine[]` param) actually filters results.
// This is a UI-completeness vs. fabricated-behavior tradeoff, not a bug:
// the fields don't silently do nothing forever, they're wired the moment
// a geocoding/text-search endpoint exists.
import { useRouter } from "next/navigation";
import { useState } from "react";
import { CUISINE_FILTER_CHIPS } from "@/lib/constants/cuisineFilters";
import { LocationPinIcon, SearchIcon } from "@/components/ui/icons";

interface SearchFilterBarProps {
  initialLocation: string;
  initialQuery: string;
  initialCuisine: string | null;
}

/** Builds the `/search` URL for a given filter combination, resetting
 * pagination to page 1 — shared by the text-field submit and the cuisine
 * chip click below so both stay consistent. */
function buildSearchUrl(location: string, query: string, cuisine: string | null): string {
  const params = new URLSearchParams();
  if (location.trim()) params.set("location", location.trim());
  if (query.trim()) params.set("q", query.trim());
  if (cuisine) params.set("cuisine", cuisine);
  const qs = params.toString();
  return qs ? `/search?${qs}` : "/search";
}

export default function SearchFilterBar({
  initialLocation,
  initialQuery,
  initialCuisine,
}: SearchFilterBarProps) {
  const router = useRouter();
  const [location, setLocation] = useState(initialLocation);
  const [query, setQuery] = useState(initialQuery);
  const [selectedCuisine, setSelectedCuisine] = useState<string | null>(initialCuisine);

  function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    router.push(buildSearchUrl(location, query, selectedCuisine));
  }

  // Cuisine chips filter immediately on click (no extra "Search" press
  // needed) — the text fields above still require the submit button,
  // matching Hero's existing UX for those two inputs.
  function handleChipClick(name: string | null) {
    setSelectedCuisine(name);
    router.push(buildSearchUrl(location, query, name));
  }

  return (
    <div>
      <form
        onSubmit={handleSubmit}
        className="mx-auto flex max-w-3xl flex-col gap-3 rounded-brand-card border border-brand-border bg-white p-3 shadow-brand-card sm:flex-row sm:items-center sm:gap-2"
      >
        <label className="flex flex-1 items-center gap-2 rounded-brand-control px-3 py-2.5 sm:border-r sm:border-brand-border">
          <LocationPinIcon className="h-5 w-5 shrink-0 text-brand-ink-subtle" />
          <span className="sr-only">Location</span>
          <input
            type="text"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            placeholder="City, ZIP, or neighborhood"
            className="w-full min-w-0 border-0 bg-transparent text-sm text-brand-ink placeholder:text-brand-placeholder focus:outline-none"
          />
        </label>

        <label className="flex flex-1 items-center gap-2 rounded-brand-control px-3 py-2.5">
          <SearchIcon className="h-5 w-5 shrink-0 text-brand-ink-subtle" />
          <span className="sr-only">Cuisine, dish, or restaurant</span>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Cuisine, dish, or restaurant"
            className="w-full min-w-0 border-0 bg-transparent text-sm text-brand-ink placeholder:text-brand-placeholder focus:outline-none"
          />
        </label>

        <button
          type="submit"
          className="flex min-h-[44px] items-center justify-center gap-2 whitespace-nowrap rounded-brand-control bg-brand-accent px-6 text-sm font-semibold text-white transition hover:bg-brand-accent-hover"
        >
          <SearchIcon className="h-4 w-4" />
          Search
        </button>
      </form>

      <div
        role="group"
        aria-label="Filter by cuisine"
        className="mx-auto mt-4 flex max-w-3xl flex-wrap gap-2"
      >
        {CUISINE_FILTER_CHIPS.map((chip) => {
          const isSelected =
            chip.name === selectedCuisine ||
            (chip.name === null && selectedCuisine === null);
          return (
            <button
              key={chip.display_name}
              type="button"
              aria-pressed={isSelected}
              onClick={() => handleChipClick(chip.name)}
              className={
                isSelected
                  ? "min-h-[36px] rounded-brand-pill bg-brand-ink px-4 text-sm font-medium text-brand-bg transition"
                  : "min-h-[36px] rounded-brand-pill bg-brand-chip px-4 text-sm font-medium text-brand-chip-ink transition hover:bg-brand-chip/80"
              }
            >
              {chip.display_name}
            </button>
          );
        })}
      </div>
    </div>
  );
}
