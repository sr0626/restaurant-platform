"use client";

// Admin claim review UI.
//
// FLAGGED CONTRACT GAP (see PR description): docs/API_CONTRACTS.md's
// "Claim flow (`/claim`)" section only documents `GET /claim/{id}` — a
// single claim by id, readable by its claimant or an admin. There is no
// `GET /claim` (list) or `GET /claim?status=pending_review` endpoint, so
// there is no real data source for "the admin queue" as a list. Rather
// than fabricate a list from nothing, this is a lookup-by-id tool: an
// admin enters a claim id (e.g. from the id a claimant would see on their
// own pending-review confirmation, or from a support request) and reviews/
// approves/rejects that one claim. Claims looked up in a session are kept
// in local state below so an admin working through several ids in one
// sitting doesn't lose earlier results — that's a client-side convenience
// list of what *this admin already fetched*, not a fabricated server list.
// A real queue needs a new backend endpoint (e.g. `GET /claim?status=
// pending_review`) — flagged for Architect/Backend Dev, not built here.
import { useState } from "react";
import {
  approveClaimAction,
  lookupClaimAction,
  rejectClaimAction,
} from "@/app/admin/claims/actions";
import ClaimStatusBadge from "@/components/claim/ClaimStatusBadge";
import { CheckIcon, XIcon } from "@/components/ui/icons";
import type { ClaimResponse } from "@/types/claim";

type ReviewedClaim = ClaimResponse & { _reviewedAt: number };

function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export default function ClaimReviewPanel() {
  const [claimIdInput, setClaimIdInput] = useState("");
  const [lookupError, setLookupError] = useState<string | null>(null);
  const [looking, setLooking] = useState(false);
  const [claims, setClaims] = useState<ReviewedClaim[]>([]);
  const [activeClaimId, setActiveClaimId] = useState<number | null>(null);

  const activeClaim = claims.find((c) => c.claim_id === activeClaimId) ?? null;

  function upsertClaim(claim: ClaimResponse) {
    setClaims((prev) => {
      const withoutExisting = prev.filter((c) => c.claim_id !== claim.claim_id);
      return [{ ...claim, _reviewedAt: Date.now() }, ...withoutExisting];
    });
    setActiveClaimId(claim.claim_id);
  }

  async function handleLookup(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLookupError(null);
    const claimId = Number.parseInt(claimIdInput, 10);
    if (!Number.isFinite(claimId) || claimId <= 0) {
      setLookupError("Enter a valid claim id.");
      return;
    }

    setLooking(true);
    try {
      const result = await lookupClaimAction(claimId);
      if (result.ok) {
        upsertClaim(result.claim);
        setClaimIdInput("");
      } else {
        setLookupError(result.error);
      }
    } finally {
      setLooking(false);
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="rounded-brand-card border border-dashed border-brand-border bg-white p-5">
        <p className="font-display text-sm font-semibold text-brand-ink">
          No list-all-pending endpoint exists yet
        </p>
        <p className="mt-1 text-sm text-brand-ink-muted">
          The current <code className="text-brand-ink">/claim</code> contract only supports
          looking up one claim by id — there is no endpoint to list every pending claim.
          Look up claims by id below (e.g. the id a claimant sees on their submission
          confirmation). See this PR&apos;s description for the flagged gap and the
          suggested endpoint to close it.
        </p>
      </div>

      <form onSubmit={handleLookup} className="flex flex-col gap-2 sm:flex-row sm:items-end">
        <div className="flex-1">
          <label htmlFor="claim_id" className="text-sm font-semibold text-brand-ink">
            Claim ID
          </label>
          <input
            id="claim_id"
            type="number"
            min={1}
            value={claimIdInput}
            onChange={(e) => setClaimIdInput(e.target.value)}
            placeholder="e.g. 789"
            className="mt-2 w-full rounded-brand-control border border-brand-border bg-white px-3 py-2.5 text-sm text-brand-ink placeholder:text-brand-placeholder focus:border-brand-accent focus:outline-none"
          />
        </div>
        <button
          type="submit"
          disabled={looking}
          className="flex min-h-[44px] items-center justify-center rounded-brand-control bg-brand-ink px-6 text-sm font-semibold text-brand-bg transition hover:bg-brand-ink/90 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {looking ? "Looking up..." : "Look up claim"}
        </button>
      </form>
      {lookupError && (
        <p className="rounded-brand-control bg-brand-closed-bg px-3 py-2.5 text-sm text-brand-closed">
          {lookupError}
        </p>
      )}

      {claims.length > 0 && (
        <div className="flex flex-col gap-3">
          <p className="text-sm font-semibold text-brand-ink-subtle">
            Looked up this session
          </p>
          <ul className="flex flex-col gap-2">
            {claims.map((claim) => (
              <li key={claim.claim_id}>
                <button
                  type="button"
                  onClick={() => setActiveClaimId(claim.claim_id)}
                  className={
                    claim.claim_id === activeClaimId
                      ? "flex w-full items-center justify-between rounded-brand-control border-2 border-brand-accent bg-brand-bg px-4 py-3 text-left"
                      : "flex w-full items-center justify-between rounded-brand-control border border-brand-border bg-white px-4 py-3 text-left transition hover:border-brand-ink-subtle"
                  }
                >
                  <span className="text-sm font-medium text-brand-ink">
                    Claim #{claim.claim_id} — brand #{claim.brand_id}
                  </span>
                  <ClaimStatusBadge status={claim.status} />
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      {activeClaim && (
        <ClaimDetailCard
          claim={activeClaim}
          onApprove={(updated) => upsertClaim(updated)}
          onReject={(updated) => upsertClaim(updated)}
        />
      )}
    </div>
  );
}

function ClaimDetailCard({
  claim,
  onApprove,
  onReject,
}: {
  claim: ClaimResponse;
  onApprove: (claim: ClaimResponse) => void;
  onReject: (claim: ClaimResponse) => void;
}) {
  const [approveNotes, setApproveNotes] = useState("");
  const [rejectNotes, setRejectNotes] = useState("");
  const [confirmingReject, setConfirmingReject] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [pendingAction, setPendingAction] = useState<"approve" | "reject" | null>(null);

  const isPending = claim.status === "pending_review";

  async function handleApprove() {
    setActionError(null);
    setPendingAction("approve");
    try {
      const result = await approveClaimAction(claim.claim_id, approveNotes.trim());
      if (result.ok) {
        onApprove(result.claim);
      } else {
        setActionError(result.error);
      }
    } finally {
      setPendingAction(null);
    }
  }

  async function handleReject() {
    if (!confirmingReject) {
      setConfirmingReject(true);
      return;
    }
    setActionError(null);
    if (!rejectNotes.trim()) {
      setActionError("Reviewer notes are required to reject a claim.");
      return;
    }
    setPendingAction("reject");
    try {
      const result = await rejectClaimAction(claim.claim_id, rejectNotes.trim());
      if (result.ok) {
        onReject(result.claim);
        setConfirmingReject(false);
      } else {
        setActionError(result.error);
      }
    } finally {
      setPendingAction(null);
    }
  }

  return (
    <div className="rounded-brand-card border border-brand-border bg-white p-6 shadow-brand-card">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="font-display text-lg font-bold text-brand-ink">
          Claim #{claim.claim_id}
        </h2>
        <ClaimStatusBadge status={claim.status} />
      </div>

      <dl className="mt-4 grid grid-cols-1 gap-3 rounded-brand-control bg-brand-bg p-4 text-sm sm:grid-cols-2">
        <div>
          <dt className="text-brand-ink-subtle">Brand ID</dt>
          <dd className="mt-1 font-medium text-brand-ink">#{claim.brand_id}</dd>
        </div>
        <div>
          <dt className="text-brand-ink-subtle">Proof method</dt>
          <dd className="mt-1 font-medium text-brand-ink">
            {claim.proof_method.replace(/_/g, " ")}
          </dd>
        </div>
        <div>
          <dt className="text-brand-ink-subtle">Submitted</dt>
          <dd className="mt-1 font-medium text-brand-ink">
            {formatDateTime(claim.submitted_at)}
          </dd>
        </div>
        <div>
          <dt className="text-brand-ink-subtle">SLA due</dt>
          <dd className="mt-1 font-medium text-brand-ink">
            {formatDateTime(claim.sla_due_at)}
          </dd>
        </div>
        {claim.reviewed_at && (
          <div>
            <dt className="text-brand-ink-subtle">Reviewed</dt>
            <dd className="mt-1 font-medium text-brand-ink">
              {formatDateTime(claim.reviewed_at)}
            </dd>
          </div>
        )}
        {claim.reviewer_notes && (
          <div className="sm:col-span-2">
            <dt className="text-brand-ink-subtle">Reviewer notes</dt>
            <dd className="mt-1 font-medium text-brand-ink">{claim.reviewer_notes}</dd>
          </div>
        )}
      </dl>

      {actionError && (
        <p className="mt-4 rounded-brand-control bg-brand-closed-bg px-3 py-2.5 text-sm text-brand-closed">
          {actionError}
        </p>
      )}

      {isPending && (
        <div className="mt-6 flex flex-col gap-4 border-t border-brand-border pt-5 sm:flex-row">
          <div className="flex-1">
            <label htmlFor="approve_notes" className="text-sm font-semibold text-brand-ink">
              Approve
            </label>
            <input
              id="approve_notes"
              type="text"
              value={approveNotes}
              onChange={(e) => setApproveNotes(e.target.value)}
              placeholder="Reviewer notes (optional)"
              className="mt-2 w-full rounded-brand-control border border-brand-border bg-white px-3 py-2.5 text-sm text-brand-ink placeholder:text-brand-placeholder focus:border-brand-accent focus:outline-none"
            />
            <button
              type="button"
              onClick={handleApprove}
              disabled={pendingAction !== null}
              className="mt-2 flex min-h-[44px] w-full items-center justify-center gap-2 rounded-brand-control bg-brand-success px-4 text-sm font-semibold text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
            >
              <CheckIcon className="h-4 w-4" />
              {pendingAction === "approve" ? "Approving..." : "Approve claim"}
            </button>
          </div>

          <div className="flex-1">
            <label htmlFor="reject_notes" className="text-sm font-semibold text-brand-ink">
              Reject
            </label>
            <input
              id="reject_notes"
              type="text"
              value={rejectNotes}
              onChange={(e) => setRejectNotes(e.target.value)}
              placeholder="Reviewer notes (required)"
              className="mt-2 w-full rounded-brand-control border border-brand-border bg-white px-3 py-2.5 text-sm text-brand-ink placeholder:text-brand-placeholder focus:border-brand-accent focus:outline-none"
            />
            <button
              type="button"
              onClick={handleReject}
              disabled={pendingAction !== null}
              className={
                confirmingReject
                  ? "mt-2 flex min-h-[44px] w-full items-center justify-center gap-2 rounded-brand-control bg-brand-closed px-4 text-sm font-semibold text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
                  : "mt-2 flex min-h-[44px] w-full items-center justify-center gap-2 rounded-brand-control border border-brand-closed px-4 text-sm font-semibold text-brand-closed transition hover:bg-brand-closed-bg disabled:cursor-not-allowed disabled:opacity-60"
              }
            >
              <XIcon className="h-4 w-4" />
              {pendingAction === "reject"
                ? "Rejecting..."
                : confirmingReject
                ? "Confirm reject"
                : "Reject claim"}
            </button>
            {confirmingReject && (
              <button
                type="button"
                onClick={() => setConfirmingReject(false)}
                className="mt-1 w-full text-center text-xs font-medium text-brand-ink-subtle underline"
              >
                Cancel
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
