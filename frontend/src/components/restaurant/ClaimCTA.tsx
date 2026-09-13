// Unclaimed-listing call-to-action for the public restaurant detail page.
// `restaurant_brand.owner_id` is null / `is_claimed` is false for
// admin-seeded listings nobody has claimed yet (docs/DECISIONS.md
// "owner_id nullable on restaurant_brand (unclaimed listings)"). The claim
// flow's own form/UI isn't built yet (separate later task) — this links to
// `/claim` with the brand id as a placeholder target, same judgment call
// TopBar.tsx already made for "For Owners" pointing at the not-yet-built
// `/login` destination.
import Link from "next/link";

export default function ClaimCTA({ brandId }: { brandId: number }) {
  return (
    <div className="flex flex-col items-start gap-3 rounded-brand-card border border-dashed border-brand-border bg-white p-5 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <p className="font-display text-base font-semibold text-brand-ink">
          Is this your restaurant?
        </p>
        <p className="mt-1 text-sm text-brand-ink-muted">
          This listing hasn&apos;t been claimed yet. Claim it to manage hours,
          photos, and more.
        </p>
      </div>
      <Link
        href={`/claim?brand_id=${brandId}`}
        className="flex min-h-[44px] shrink-0 items-center whitespace-nowrap rounded-brand-pill bg-brand-ink px-5 text-sm font-semibold text-brand-bg transition hover:bg-brand-ink/90"
      >
        Claim this restaurant
      </Link>
    </div>
  );
}
