import RestaurantCardSkeleton from "./RestaurantCardSkeleton";

/** Suspense fallback for <PopularNearYou> — grid of skeleton cards, same
 * responsive column count as the real grid so there's no layout jump. */
export default function PopularNearYouSkeleton() {
  return (
    <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: 6 }).map((_, i) => (
        <RestaurantCardSkeleton key={i} />
      ))}
    </div>
  );
}
