// Server component that fetches the real search results grid via the
// typed GET /search client, same graceful-degradation posture as the
// homepage's `PopularNearYou` (frontend/CLAUDE.md "ALWAYS handle API
// errors gracefully" / no fabricated restaurant data ever).
import { searchRestaurants } from "@/lib/api/search";
import RestaurantCard from "@/components/listing/RestaurantCard";
import InfoPanel from "@/components/ui/InfoPanel";
import Pagination from "@/components/search/Pagination";

/** Matches docs/API_CONTRACTS.md "GET /search" default page_size. */
export const SEARCH_PAGE_SIZE = 20;

interface SearchResultsProps {
  cuisine: string | null;
  page: number;
  /** Carried through to pagination links only — see SearchFilterBar's
   * note on why these aren't sent to the API itself. */
  location: string;
  query: string;
}

export default async function SearchResults({ cuisine, page, location, query }: SearchResultsProps) {
  let data;
  try {
    data = await searchRestaurants({
      cuisine: cuisine ? [cuisine] : undefined,
      page,
      page_size: SEARCH_PAGE_SIZE,
    });
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
        title="No restaurants match your search"
        body="Try a different cuisine filter, or clear your filters to see everything nearby."
      />
    );
  }

  return (
    <div>
      <p className="mb-4 text-sm text-brand-ink-muted">
        {data.total} restaurant{data.total === 1 ? "" : "s"} found
      </p>

      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {data.results.map((item) => (
          <RestaurantCard key={item.brand_id} item={item} />
        ))}
      </div>

      <Pagination
        page={data.page}
        pageSize={data.page_size}
        total={data.total}
        extraParams={{ location, q: query, cuisine }}
      />
    </div>
  );
}
