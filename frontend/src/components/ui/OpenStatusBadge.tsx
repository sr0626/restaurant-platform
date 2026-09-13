// Shared open/closed status pill — extracted from `RestaurantCard` so the
// public restaurant detail page's hero can reuse the exact same styling
// (task brief: "is_open_now status badge (reuse the open/closed badge
// styling from RestaurantCard)") instead of forking a second copy.
export default function OpenStatusBadge({
  isOpenNow,
}: {
  isOpenNow: boolean | null;
}) {
  if (isOpenNow === null) {
    return (
      <span className="inline-flex items-center rounded-brand-pill bg-brand-chip px-2.5 py-1 text-xs font-semibold text-brand-ink-subtle">
        Hours unknown
      </span>
    );
  }
  if (isOpenNow) {
    return (
      <span className="inline-flex items-center rounded-brand-pill bg-brand-success-bg px-2.5 py-1 text-xs font-semibold text-brand-success">
        Open Now
      </span>
    );
  }
  return (
    <span className="inline-flex items-center rounded-brand-pill bg-brand-closed-bg px-2.5 py-1 text-xs font-semibold text-brand-closed">
      Closed
    </span>
  );
}
