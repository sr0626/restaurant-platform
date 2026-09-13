// Cognito configuration. Never hardcode a pool ID or client ID (root
// CLAUDE.md "AWS Best Practices" / frontend/CLAUDE.md "Environment
// Variables") — always read from NEXT_PUBLIC_ env vars.

export const cognitoConfig = {
  userPoolId: process.env.NEXT_PUBLIC_COGNITO_USER_POOL_ID,
  clientId: process.env.NEXT_PUBLIC_COGNITO_CLIENT_ID,
} as const;

export interface ResolvedCognitoConfig {
  userPoolId: string;
  clientId: string;
}

/** Throws with a clear message instead of failing deep inside a verifier call. */
export function assertCognitoConfig(): ResolvedCognitoConfig {
  const { userPoolId, clientId } = cognitoConfig;
  if (!userPoolId || !clientId) {
    throw new Error(
      "Cognito is not configured — set NEXT_PUBLIC_COGNITO_USER_POOL_ID and NEXT_PUBLIC_COGNITO_CLIENT_ID."
    );
  }
  return { userPoolId, clientId };
}
