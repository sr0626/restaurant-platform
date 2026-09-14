// Shared claim-status pill — same visual pattern as
// `components/ui/OpenStatusBadge.tsx` (rounded-brand-pill + a semantic
// color pair per state) but for `ClaimStatus` instead of open/closed.
// Used by both the claimant's own submit-confirmation view and the admin
// review queue so the same status always reads the same way.
import type { ClaimStatus } from "@/types/claim";

const STATUS_COPY: Record<ClaimStatus, string> = {
  pending_review: "Pending Review",
  approved: "Approved",
  rejected: "Rejected",
};

export default function ClaimStatusBadge({ status }: { status: ClaimStatus }) {
  if (status === "approved") {
    return (
      <span className="inline-flex items-center rounded-brand-pill bg-brand-success-bg px-2.5 py-1 text-xs font-semibold text-brand-success">
        {STATUS_COPY.approved}
      </span>
    );
  }
  if (status === "rejected") {
    return (
      <span className="inline-flex items-center rounded-brand-pill bg-brand-closed-bg px-2.5 py-1 text-xs font-semibold text-brand-closed">
        {STATUS_COPY.rejected}
      </span>
    );
  }
  return (
    <span className="inline-flex items-center rounded-brand-pill bg-brand-chip px-2.5 py-1 text-xs font-semibold text-brand-chip-ink">
      {STATUS_COPY.pending_review}
    </span>
  );
}
