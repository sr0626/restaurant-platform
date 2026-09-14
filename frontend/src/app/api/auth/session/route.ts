// POST /api/auth/session — the missing half of the auth scaffold that
// shipped in the original frontend PR (lib/auth/session.ts's
// `getServerSession()` could only ever read a session cookie, never set
// one — see that file's history).
//
// The client-side sign-in form (components/auth/LoginForm.tsx)
// authenticates against Cognito directly via @aws-amplify/auth, then POSTs
// the access token it gets back here. This route re-verifies that token
// server-side (via `resolveSession()`, the same aws-jwt-verify logic
// `getServerSession()` uses) before trusting it enough to set it as the
// secure, httpOnly `rp_access_token` cookie — the token never sits in
// localStorage at any point in this flow (frontend/CLAUDE.md "NEVER store
// auth tokens in localStorage — use Cognito's secure cookie approach").
import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import {
  resolveSession,
  SESSION_COOKIE_NAME,
  SESSION_MAX_AGE_SECONDS,
} from "@/lib/auth/session";

export async function POST(request: Request) {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Invalid request." }, { status: 400 });
  }

  const accessToken =
    body && typeof body === "object" && "accessToken" in body
      ? (body as { accessToken: unknown }).accessToken
      : undefined;

  if (typeof accessToken !== "string" || accessToken.length === 0) {
    return NextResponse.json({ error: "Invalid request." }, { status: 400 });
  }

  const session = await resolveSession(accessToken);
  if (!session) {
    // Generic message — never surface verifier internals (root CLAUDE.md
    // "NEVER expose internal stack details in API error responses").
    return NextResponse.json(
      { error: "Could not establish session." },
      { status: 401 }
    );
  }

  cookies().set(SESSION_COOKIE_NAME, accessToken, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: SESSION_MAX_AGE_SECONDS,
  });

  // Only the role is returned — enough for the client to pick a landing
  // page (LoginForm.tsx), nothing more sensitive than what's already in
  // the JWT the client itself just supplied.
  return NextResponse.json({ role: session.role });
}
