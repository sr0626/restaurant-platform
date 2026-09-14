// Real Cognito sign-in page — replaces the bare placeholder Architect's
// review flagged. Reuses the shared TopBar (components/home/TopBar.tsx)
// for consistency with the rest of the "Spice Market" direction, and a
// centered card using the same rounded-brand-card/shadow-brand-card
// treatment as components/restaurant/ClaimCTA.tsx and the Hero search bar.
// The actual form/Cognito wiring lives in components/auth/LoginForm.tsx (a
// client component — @aws-amplify/auth only runs in the browser); this
// page itself needs no data fetching, so it stays a plain Server Component
// for the metadata/layout shell.
import type { Metadata } from "next";
import TopBar from "@/components/home/TopBar";
import LoginForm from "@/components/auth/LoginForm";

export const metadata: Metadata = {
  title: "Sign In",
};

export default function LoginPage() {
  return (
    <main className="min-h-screen bg-brand-bg">
      <TopBar />

      <div className="mx-auto flex max-w-6xl justify-center px-4 py-12 sm:px-6 sm:py-16">
        <div className="w-full max-w-md rounded-brand-card border border-brand-border bg-white p-6 shadow-brand-card sm:p-8">
          <h1 className="font-display text-2xl font-bold text-brand-ink">
            Sign In
          </h1>
          <p className="mt-1 text-sm text-brand-ink-muted">
            Sign in to manage your restaurant listing or continue as a
            registered user.
          </p>

          <div className="mt-6">
            <LoginForm />
          </div>
        </div>
      </div>
    </main>
  );
}
