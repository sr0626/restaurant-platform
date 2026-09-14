"use client";

// Real Cognito sign-in form for the "Spice Market" login page
// (app/login/page.tsx).
//
// JUDGMENT CALL (flagged in final report): lib/auth/config.ts only ever
// defines `userPoolId`/`clientId` — no hostedUIUrl, Cognito domain, or
// redirect URI, and infra/modules/cognito/main.tf never provisions a
// Hosted UI domain either. frontend/CLAUDE.md's Stack section names
// "amazon-cognito-identity-js or @aws-amplify/auth" as the intended
// mechanism, and @aws-amplify/auth is the one already pinned in
// package.json. So this is the client-side email/password form via
// @aws-amplify/auth, not a Hosted UI redirect.
//
// Tokens never touch localStorage — see lib/auth/amplifyClient.ts's
// in-memory KeyValueStorage override. After signIn() succeeds, the access
// token is handed to POST /api/auth/session (app/api/auth/session/route.ts)
// which verifies it and sets the real httpOnly session cookie
// getServerSession()/requireSession() read; only then do we navigate to a
// role-based landing page.
import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { signIn, fetchAuthSession } from "@aws-amplify/auth";
import { ensureAmplifyConfigured } from "@/lib/auth/amplifyClient";
import { signInSchema, type SignInFormValues } from "@/lib/validation/auth";
import type { UserRole } from "@/types/auth";

/**
 * Where each pool group lands after sign-in. Owner/manager share the
 * portal dashboard (frontend/CLAUDE.md's "Auth-gated portal pages"
 * pattern); admin has its own section; a registered_user has no gated
 * area yet in Phase 1, so it goes back to the homepage.
 */
const ROLE_LANDING: Record<UserRole, string> = {
  owner: "/portal/dashboard",
  manager: "/portal/dashboard",
  admin: "/admin/listings",
  registered_user: "/",
};

type FieldErrors = Partial<Record<keyof SignInFormValues, string>>;

export default function LoginForm() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setFormError(null);

    const parsed = signInSchema.safeParse({ email, password });
    if (!parsed.success) {
      const errors: FieldErrors = {};
      for (const issue of parsed.error.issues) {
        const key = issue.path[0] as keyof SignInFormValues;
        if (!errors[key]) errors[key] = issue.message;
      }
      setFieldErrors(errors);
      return;
    }
    setFieldErrors({});
    setSubmitting(true);

    try {
      ensureAmplifyConfigured();
      const { isSignedIn, nextStep } = await signIn({
        username: parsed.data.email,
        password: parsed.data.password,
      });

      if (!isSignedIn) {
        setFormError(messageForNextStep(nextStep.signInStep));
        setSubmitting(false);
        return;
      }

      const authSession = await fetchAuthSession();
      const accessToken = authSession.tokens?.accessToken?.toString();
      if (!accessToken) {
        setFormError(
          "Sign-in succeeded but no session token was returned. Please try again."
        );
        setSubmitting(false);
        return;
      }

      const res = await fetch("/api/auth/session", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ accessToken }),
      });

      if (!res.ok) {
        setFormError("Could not establish your session. Please try again.");
        setSubmitting(false);
        return;
      }

      const { role } = (await res.json()) as { role: UserRole };
      router.push(ROLE_LANDING[role] ?? "/");
      router.refresh();
    } catch (err) {
      setFormError(messageForAuthError(err));
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4" noValidate>
      {formError && (
        <p
          role="alert"
          className="rounded-brand-control bg-brand-closed-bg px-3 py-2 text-sm text-brand-closed"
        >
          {formError}
        </p>
      )}

      <div className="flex flex-col gap-1.5">
        <label
          htmlFor="email"
          className="text-sm font-medium text-brand-ink-muted"
        >
          Email
        </label>
        <input
          id="email"
          name="email"
          type="email"
          autoComplete="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          aria-invalid={Boolean(fieldErrors.email)}
          className="min-h-[44px] rounded-brand-control border border-brand-border bg-white px-3 text-sm text-brand-ink placeholder:text-brand-placeholder focus:outline-none focus:ring-2 focus:ring-brand-accent"
          placeholder="you@example.com"
        />
        {fieldErrors.email && (
          <p className="text-sm text-brand-closed">{fieldErrors.email}</p>
        )}
      </div>

      <div className="flex flex-col gap-1.5">
        <label
          htmlFor="password"
          className="text-sm font-medium text-brand-ink-muted"
        >
          Password
        </label>
        <input
          id="password"
          name="password"
          type="password"
          autoComplete="current-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          aria-invalid={Boolean(fieldErrors.password)}
          className="min-h-[44px] rounded-brand-control border border-brand-border bg-white px-3 text-sm text-brand-ink placeholder:text-brand-placeholder focus:outline-none focus:ring-2 focus:ring-brand-accent"
          placeholder="********"
        />
        {fieldErrors.password && (
          <p className="text-sm text-brand-closed">{fieldErrors.password}</p>
        )}
      </div>

      <button
        type="submit"
        disabled={submitting}
        className="flex min-h-[44px] items-center justify-center whitespace-nowrap rounded-brand-control bg-brand-accent px-6 text-sm font-semibold text-white transition hover:bg-brand-accent-hover disabled:cursor-not-allowed disabled:opacity-60"
      >
        {submitting ? "Signing in…" : "Sign In"}
      </button>
    </form>
  );
}

/** Non-DONE sign-in steps we can explain without building a full challenge UI (out of Phase 1 scope). */
function messageForNextStep(step: string): string {
  switch (step) {
    case "CONFIRM_SIGN_UP":
      return "Please confirm your email before signing in.";
    case "RESET_PASSWORD":
    case "CONFIRM_SIGN_IN_WITH_NEW_PASSWORD_REQUIRED":
      return "Your password needs to be reset before you can sign in. Contact support for help.";
    default:
      return "Additional verification is required to finish signing in.";
  }
}

/** Maps known Cognito error names to friendly copy — never surface raw SDK messages (root CLAUDE.md "NEVER expose internal stack details"). */
function messageForAuthError(err: unknown): string {
  const name = err instanceof Error ? err.name : "";
  switch (name) {
    case "UserNotFoundException":
    case "NotAuthorizedException":
      return "Incorrect email or password.";
    case "UserNotConfirmedException":
      return "Please confirm your email before signing in.";
    case "TooManyRequestsException":
    case "LimitExceededException":
      return "Too many attempts. Please wait a moment and try again.";
    default:
      return "Something went wrong signing in. Please try again.";
  }
}
