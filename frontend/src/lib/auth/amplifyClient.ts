"use client";

// Client-side Amplify bootstrap for the sign-in form only
// (components/auth/LoginForm.tsx). Deliberately NOT re-exported from
// lib/auth/index.ts's barrel — everything else in lib/auth/ is server-only
// (session.ts/guards.ts use `next/headers`), and this file configures a
// browser-only Amplify singleton, so keeping it off the barrel means no
// Server Component can accidentally pull it in.
//
// @aws-amplify/auth's default Cognito token store falls back to
// `window.localStorage` when available (see its own tokenProvider.mjs doc
// comment: "It stores the tokens in `window.localStorage` if available").
// That would violate frontend/CLAUDE.md's "NEVER store auth tokens in
// localStorage — use Cognito's secure cookie approach", so this swaps in
// an in-memory store before any sign-in call: tokens live only for the
// instant between `signIn()`/`fetchAuthSession()` and handing the access
// token to POST /api/auth/session, which sets the real httpOnly cookie.
// Nothing Amplify touches here ever reaches disk.
import { Amplify, type KeyValueStorageInterface } from "@aws-amplify/core";
import { cognitoUserPoolsTokenProvider } from "@aws-amplify/auth/cognito";
import { assertCognitoConfig } from "./config";

class InMemoryKeyValueStorage implements KeyValueStorageInterface {
  private readonly store = new Map<string, string>();

  async getItem(key: string): Promise<string | null> {
    return this.store.has(key) ? (this.store.get(key) as string) : null;
  }

  async setItem(key: string, value: string): Promise<void> {
    this.store.set(key, value);
  }

  async removeItem(key: string): Promise<void> {
    this.store.delete(key);
  }

  async clear(): Promise<void> {
    this.store.clear();
  }
}

let configured = false;

/**
 * Configures Amplify's Cognito user pool once for this browser tab. Safe
 * to call on every sign-in attempt — a no-op after the first call.
 */
export function ensureAmplifyConfigured(): void {
  if (configured) return;

  const { userPoolId, clientId } = assertCognitoConfig();

  cognitoUserPoolsTokenProvider.setKeyValueStorage(
    new InMemoryKeyValueStorage()
  );

  Amplify.configure({
    Auth: {
      Cognito: {
        userPoolId,
        userPoolClientId: clientId,
      },
    },
  });

  configured = true;
}
