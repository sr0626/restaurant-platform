// Restaurant card for the homepage's "Popular near you" grid.
//
// NOTE (flagged in final report): the approved mockup calls for a star
// rating on each card, but neither `SearchResultItem` (docs/API_CONTRACTS.md
// "GET /search") nor `docs/DATA_MODEL.md` has a rating/review field in
// Phase 1 — there is no reviews feature yet. Showing a star score here
// would mean fabricating data, which the task explicitly rules out, so the
// numeric rating is omitted. The star glyph the design calls for is still
// built (`StarIcon`) and used on the "Featured" ribbon instead, so the
// icon requirement is met without inventing a number.
import Link from "next/link";
import type { SearchResultItem } from "@/types/search";
import { LocationPinIcon, StarIcon } from "@/components/ui/icons";
import OpenStatusBadge from "@/components/ui/OpenStatusBadge";

export default function RestaurantCard({ item }: { item: SearchResultItem }) {
  const { nearest_location } = item;
  const visibleTags = item.cuisine_tags.slice(0, 3);

  return (
    <Link
      href={`/restaurant/${item.slug}`}
      className="group flex flex-col overflow-hidden rounded-brand-card border border-brand-border bg-white shadow-brand-card transition hover:shadow-brand-card-hover"
    >
      <div className="relative h-40 w-full shrink-0 bg-brand-warm-gradient">
        {nearest_location.is_paid && (
          <span className="absolute left-3 top-3 inline-flex items-center gap-1 rounded-brand-pill bg-brand-ink/85 px-2.5 py-1 text-xs font-semibold text-brand-bg">
            <StarIcon className="h-3 w-3" />
            Featured
          </span>
        )}
      </div>

      <div className="flex flex-1 flex-col gap-2 p-4">
        <h3 className="font-display text-lg font-semibold text-brand-ink">
          {item.name}
        </h3>

        {visibleTags.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {visibleTags.map((tag) => (
              <span
                key={tag.name}
                className="rounded-brand-pill bg-brand-chip px-2 py-0.5 text-xs font-medium text-brand-chip-ink"
              >
                {tag.display_name}
              </span>
            ))}
          </div>
        )}

        <div className="mt-1 flex items-center gap-1 text-sm text-brand-ink-subtle">
          <LocationPinIcon className="h-4 w-4 shrink-0" />
          <span>
            {nearest_location.city}, {nearest_location.state} ·{" "}
            {nearest_location.distance_mi.toFixed(1)} mi
          </span>
        </div>

        {item.location_count_nearby > 1 && (
          <p className="text-xs text-brand-ink-subtle">
            {item.location_count_nearby} locations nearby
          </p>
        )}

        <div className="mt-auto flex items-center justify-between pt-2">
          <OpenStatusBadge isOpenNow={nearest_location.is_open_now} />
          {!item.is_claimed && (
            <span className="text-xs font-medium text-brand-ink-subtle">
              Unclaimed
            </span>
          )}
        </div>
      </div>
    </Link>
  );
}
