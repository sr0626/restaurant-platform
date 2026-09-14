// Homepage top bar: wordmark + tagline, nav links, "Add Your Restaurant" CTA.
//
// JUDGMENT CALL (flagged in final report): "For Owners", "Sign In", and
// "Add Your Restaurant" all point at `/login` — the only real auth entry
// point that exists yet (frontend/src/app/login/page.tsx is a placeholder;
// the owner-onboarding/claim flow isn't built in this task's scope). Once a
// dedicated owners-landing or claim-flow route exists, repoint these.
import Link from "next/link";

export default function TopBar() {
  return (
    <header className="border-b border-brand-border bg-brand-bg">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-4 sm:px-6">
        <div className="flex flex-col leading-tight">
          <span className="font-display text-xl font-bold text-brand-ink sm:text-2xl">
            Swaad
          </span>
          <span className="text-[10px] font-semibold uppercase tracking-[0.14em] text-brand-ink-subtle sm:text-xs">
            Discover Your Taste
          </span>
        </div>

        <nav className="hidden items-center gap-6 text-sm font-medium text-brand-ink-muted sm:flex">
          <Link href="/login" className="transition hover:text-brand-ink">
            For Owners
          </Link>
          <Link href="/login" className="transition hover:text-brand-ink">
            Sign In
          </Link>
        </nav>

        <Link
          href="/login"
          className="flex min-h-[44px] items-center whitespace-nowrap rounded-brand-pill bg-brand-ink px-4 text-sm font-semibold text-brand-bg transition hover:bg-brand-ink/90 sm:px-5"
        >
          Add Your Restaurant
        </Link>
      </div>
    </header>
  );
}
