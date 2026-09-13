// Homepage cuisine filter chips.
//
// FLAGGED GAP (see final report): there is no public "list cuisine tags"
// endpoint in docs/API_CONTRACTS.md — `cuisine_tag` rows are admin-managed
// only (docs/TAXONOMY.md "Seed Script Notes"), so this list can't be fetched
// live yet. These are real `cuisine_tag.name` / `display_name` values taken
// directly from docs/TAXONOMY.md (not invented), scoped to the handful most
// useful as homepage quick filters. When a public cuisine-tag list endpoint
// exists, swap this constant for a fetch.
//
// Note: the approved mockup's "Pure Vegetarian" chip is renamed to
// "Vegetarian" here to match the actual `dietary` tag's `display_name` in
// docs/TAXONOMY.md — there is no separate "pure_vegetarian" tag.
import type { CuisineCategory } from "@/types/cuisine";

export interface CuisineFilterChip {
  /** `cuisine_tag.name` — omitted for the synthetic "All Cuisines" chip. */
  name: string | null;
  display_name: string;
  category: CuisineCategory | null;
}

export const CUISINE_FILTER_CHIPS: CuisineFilterChip[] = [
  { name: null, display_name: "All Cuisines", category: null },
  { name: "north_indian", display_name: "North Indian", category: "regional" },
  { name: "south_indian", display_name: "South Indian", category: "regional" },
  { name: "hyderabadi", display_name: "Hyderabadi", category: "regional" },
  { name: "street_food", display_name: "Street Food", category: "regional" },
  { name: "vegetarian", display_name: "Vegetarian", category: "dietary" },
];
