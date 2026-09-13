// Server component that fetches the real "Popular near you" grid via the
// typed GET /search client (frontend/CLAUDE.md "NEVER fetch() inline in a
// component" — this only calls the typed function).
//
// Location default: deliberately omits `lat`/`lng`. docs/API_CONTRACTS.md
// "GET /search" says an omitted lat/lng falls back server-side to the
// admin-configured DFW bounding box (docs/DECISIONS.md "Default search
// radius"; the concrete fallback point lives in
// `backend/app/services/search_service.py` as `_DEFAULT_LAT`/`_DEFAULT_LNG`).
// Duplicating that literal here would create two sources of truth for the
// same default — letting the backend apply its own documented fallback is
// the more maintainable choice for this early build.
//
// The backend has no deployed AWS resources yet (root CLAUDE.md "Current
// Phase" / this task's brief) — this fetch is expected to fail or hang in
// any live preview until that changes. Errors are caught and rendered as a
// friendly empty state, never a broken page, and a zero-result response
// gets its own distinct "nothing found" message — neither state fabricates
// restaurant data.
import { searchRestaurants } from "@/lib/api/search";
import RestaurantCard from "@/components/listing/RestaurantCard";
import InfoPanel from "@/components/ui/InfoPanel";

const POPULAR_NEAR_YOU_PAGE_SIZE = 6;

export default async function PopularNearYou() {
  let data;
  try {
    data = await searchRestaurants({ page_size: POPULAR_NEAR_YOU_PAGE_SIZE });
  } catch {
    return (
      <InfoPanel
        title="We can't load restaurants right now"
        body="Our search service is still coming online. Check back shortly, or try again in a bit."
      />
    );
  }

  if (data.results.length === 0) {
    return (
      <InfoPanel
        title="No verified restaurants here yet"
        body="We're still verifying restaurants in this area. Check back soon, or search a different city."
      />
    );
  }

  return (
    <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
      {data.results.map((item) => (
        <RestaurantCard key={item.brand_id} item={item} />
      ))}
    </div>
  );
}
