// Server-side Cognito session helper — matches the `getServerSession`
// pattern in frontend/CLAUDE.md's "Auth-gated portal pages" section.
//
// Reads the Cognito access token from a secure, httpOnly cookie and
// verifies it — never localStorage (frontend/CLAUDE.md "NEVER store auth
// tokens in localStorage — use Cognito's secure cookie approach"). Uses
// `next/headers` cookies(), so this file only works from Server Components,
// Route Handlers, and Server Actions (not Client Components) — that's the
// same boundary the auth-gated portal pattern relies on.
//
// JUDGMENT CALL (flagged in final report): the actual sign-in exchange that
// sets this cookie (Cognito Hosted UI / SDK code exchange -> Set-Cookie) is
// not built in this task — only the read side. `aws-jwt-verify` is added
// as a new dependency for server-side JWT verification; it's the
// standard lightweight library for this and pairs with the
// `@aws-amplify/auth` / `amazon-cognito-identity-js` client-side flow
// frontend/CLAUDE.md's Stack section already calls for.
import { cookies } from "next/headers";
import { CognitoJwtVerifier } from "aws-jwt-verify";
import { assertCognitoConfig } from "./config";
import type { Session, UserRole } from "@/types/auth";

/** Set by the (not-yet-built) sign-in flow once Cognito issues tokens. */
export const SESSION_COOKIE_NAME = "rp_access_token";

const ROLES: readonly UserRole[] = [
  "owner",
  "manager",
  "admin",
  "registered_user",
];

type CognitoAccessVerifier = ReturnType<typeof CognitoJwtVerifier.create>;
let verifier: CognitoAccessVerifier | null = null;

function getVerifier(): CognitoAccessVerifier {
  if (!verifier) {
    const { userPoolId, clientId } = assertCognitoConfig();
    verifier = CognitoJwtVerifier.create({
      userPoolId,
      tokenUse: "access",
      clientId,
    });
  }
  return verifier;
}

/** Picks the first pool group that matches one of our known roles. */
function roleFromGroups(groups: unknown): UserRole | null {
  if (!Array.isArray(groups)) return null;
  return ROLES.find((role) => groups.includes(role)) ?? null;
}

/**
 * Reads and verifies the caller's Cognito session, server-side.
 * Returns null when there's no cookie, the token is expired/invalid, or it
 * carries no recognized pool group — callers should treat that the same as
 * "signed out" and redirect("/login") (see frontend/CLAUDE.md's
 * auth-gated portal pattern), not surface a verification error to the page.
 */
export async function getServerSession(): Promise<Session | null> {
  const token = cookies().get(SESSION_COOKIE_NAME)?.value;
  if (!token) return null;

  try {
    const payload = await getVerifier().verify(token);
    const role = roleFromGroups(payload["cognito:groups"]);
    if (!role) return null;

    return {
      cognitoSub: payload.sub,
      // Cognito *access* tokens don't carry an email claim by default (ID
      // tokens do) — this is populated once the sign-in flow is built,
      // either by decoding the ID token alongside the access token here,
      // or by the caller following up with GET /auth/me.
      email: typeof payload.email === "string" ? payload.email : "",
      role,
      accessToken: token,
    };
  } catch {
    return null;
  }
}
