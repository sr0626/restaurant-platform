import RestaurantCardSkeleton from "@/components/home/RestaurantCardSkeleton";

/** Suspense fallback for <SearchResults> — same skeleton grid pattern as
 * the homepage's <PopularNearYouSkeleton>, sized to the search page's
 * larger default page size instead of the homepage's 6. */
export default function SearchResultsSkeleton() {
  return (
    <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: 9 }).map((_, i) => (
        <RestaurantCardSkeleton key={i} />
      ))}
    </div>
  );
}
