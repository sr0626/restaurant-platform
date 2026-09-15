// Login helpers for each role (tests/CLAUDE.md "/e2e/fixtures/auth.ts").
//
// BLOCKED TODAY — no real Cognito to authenticate against. There is no
// deployed Cognito user pool (docs/STATUS.md: "nothing is deployed to AWS
// yet"; infra/modules/cognito has never been `terraform apply`'d), so:
//   - There are no real test user accounts in any pool.
//   - frontend/src/components/auth/LoginForm.tsx's `signIn()` call
//     (@aws-amplify/auth) has nothing real to authenticate against —
//     driving the real login form with fake credentials only exercises the
//     "wrong password" error path, not an actual signed-in session.
//   - The session cookie itself (`rp_access_token`,
//     frontend/src/lib/auth/session.ts) is only ever set by
//     app/api/auth/session/route.ts after verifying a *real* Cognito access
//     token with `aws-jwt-verify` against the real pool's JWKS — there is
//     no supported way to mint a cookie that verification will accept
//     without a real pool issuing a real token.
//
// What would unblock this:
//   1. `terraform apply` on infra/modules/cognito for a real `dev` user
//      pool (human-run only — root CLAUDE.md "NEVER run terraform apply"),
//      creating the `owner`/`manager`/`admin`/`registered_user` groups.
//   2. Seed one confirmed test user per role in that pool (e.g. via
//      `aws cognito-idp admin-create-user` + `admin-add-user-to-group`,
//      run by a human/DevOps — QA does not hold AWS credentials, see
//      tests/CLAUDE.md "NEVER use broad/admin AWS credentials... in a test
//      fixture").
//   3. Test credentials supplied to this suite via env vars (e.g.
//      `E2E_OWNER_EMAIL`/`E2E_OWNER_PASSWORD` etc.) — NEVER hardcoded here
//      (root CLAUDE.md "NEVER hardcode secrets, keys, tokens, or passwords
//      in any file").
//
// Once that exists, `loginAs` should drive the real UI (fill
// LoginForm.tsx's #email/#password fields, submit, wait for the
// role-based redirect in ROLE_LANDING) rather than fabricate a cookie —
// that's the only way this also keeps proving the real sign-in flow works,
// not just that the app trusts a cookie.
import type { Page } from "@playwright/test";

export type Role = "owner" | "manager" | "admin" | "registered_user";

/**
 * Intentionally throws rather than silently no-op-ing or faking a session.
 * Every spec that would call this is `test.skip`/`test.fixme` today with a
 * comment pointing back here — see test_claim_flow.spec.ts,
 * test_owner_portal.spec.ts, test_manager_portal.spec.ts. If a future spec
 * calls this without first checking real Cognito is available, this
 * failure is the intended signal, not a bug.
 */
export async function loginAs(_page: Page, role: Role): Promise<void> {
  throw new Error(
    `loginAs("${role}") cannot run: no real Cognito user pool is deployed yet ` +
      "(see this file's header comment for exactly what's missing and how to " +
      "unblock it). Every spec that needs a signed-in session is test.skip'd " +
      "until then — this stub exists so the fixture's shape matches " +
      "tests/CLAUDE.md and is ready to implement for real the moment a real " +
      "pool + seeded test users exist."
  );
}
