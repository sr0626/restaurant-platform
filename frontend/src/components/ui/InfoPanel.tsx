// Shared empty/error state panel — extracted from the homepage's
// `PopularNearYou` (frontend/CLAUDE.md "ALWAYS handle API errors
// gracefully" / "no fabricated data, ever"). Reused by the search results
// page for its own empty/error states so both pages render identical
// graceful-degradation UI instead of two near-duplicate components.
export default function InfoPanel({
  title,
  body,
}: {
  title: string;
  body: string;
}) {
  return (
    <div className="rounded-brand-card border border-dashed border-brand-border bg-white px-6 py-12 text-center">
      <p className="font-display text-base font-semibold text-brand-ink">
        {title}
      </p>
      <p className="mx-auto mt-2 max-w-md text-sm text-brand-ink-muted">
        {body}
      </p>
    </div>
  );
}
