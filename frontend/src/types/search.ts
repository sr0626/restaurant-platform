// Types for GET /search, matching docs/API_CONTRACTS.md.
import type { CuisineTag } from "./cuisine";

export interface SearchParams {
  lat?: number;
  lng?: number;
  /** Miles. Defaults to 15 server-side if omitted. */
  radius?: number;
  /** cuisine_tag.name values, category=regional (also signature/dining_time). */
  cuisine?: string[];
  /** cuisine_tag.name values, category=dietary. */
  dietary?: string[];
  /** cuisine_tag.name values, category=type. */
  type?: string[];
  page?: number;
  page_size?: number;
}

export interface SearchNearestLocation {
  location_id: number;
  distance_mi: number;
  city: string;
  state: string;
  is_verified: boolean;
  is_paid: boolean;
  is_open_now: boolean | null;
}

/** One brand-level card in the search results (docs/DECISIONS.md "Brand-level search results"). */
export interface SearchResultItem {
  brand_id: number;
  name: string;
  slug: string;
  is_claimed: boolean;
  cuisine_tags: CuisineTag[];
  nearest_location: SearchNearestLocation;
  /** How many of the brand's locations fall within the search radius. */
  location_count_nearby: number;
  /** Cover photo of the nearest_location specifically — not a brand-wide concept. */
  cover_photo_url: string | null;
}

export interface SearchResponse {
  results: SearchResultItem[];
  page: number;
  page_size: number;
  total: number;
}
