// Shared fetch wrapper for every typed API function in /lib/api/.
// Nothing outside this file (and the typed functions built on it) should
// call fetch() directly — see frontend/CLAUDE.md "NEVER fetch() inline in
// a component".
//
// The backend API URL is never hardcoded — always read from the
// NEXT_PUBLIC_API_URL env var (root CLAUDE.md "AWS Best Practices" /
// frontend/CLAUDE.md "Environment Variables").

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL;

/** Thrown by apiFetch on any non-2xx response. */
export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export interface ApiFetchOptions {
  /**
   * Cognito access token for routes that require auth (docs/API_CONTRACTS.md
   * "Auth model reference"). Public GET endpoints omit this. Callers get the
   * token from `getServerSession()` (server components) or their own
   * client-side session state — this file has no opinion on where it comes
   * from, only that it's attached when present.
   */
  accessToken?: string | null;
  /** Next.js data cache revalidation window, in seconds, for GET requests. */
  revalidateSeconds?: number;
}

/**
 * Builds a query string from a flat params object. Array values (e.g.
 * cuisine[], dietary[]) are repeated as multiple same-name params, matching
 * FastAPI's default List[str] query parsing.
 */
export function toQueryString(
  params: Record<string, string | number | boolean | string[] | undefined | null>
): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null) continue;
    if (Array.isArray(value)) {
      for (const item of value) search.append(key, item);
    } else {
      search.append(key, String(value));
    }
  }
  const query = search.toString();
  return query ? `?${query}` : "";
}

async function extractErrorMessage(res: Response): Promise<string> {
  try {
    const body: unknown = await res.json();
    if (body && typeof body === "object" && "detail" in body) {
      const detail = (body as { detail: unknown }).detail;
      if (typeof detail === "string") return detail;
    }
  } catch {
    // Response body wasn't JSON (or was empty) — fall through to the
    // generic message. Never surface raw stack/body details to the UI
    // (root CLAUDE.md "NEVER expose internal stack details").
  }
  return `Request failed with status ${res.status}`;
}

/**
 * Core request helper. Every function in /lib/api/*.ts calls through this
 * — it owns the base URL, auth header, JSON encode/decode, and error
 * normalization so individual endpoint functions stay one-liners.
 */
export async function apiFetch<TResponse>(
  path: string,
  init: RequestInit = {},
  options: ApiFetchOptions = {}
): Promise<TResponse> {
  if (!API_BASE_URL) {
    throw new ApiError(
      500,
      "NEXT_PUBLIC_API_URL is not configured — set it in the environment before calling the API."
    );
  }

  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");
  if (init.body !== undefined && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (options.accessToken) {
    headers.set("Authorization", `Bearer ${options.accessToken}`);
  }

  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers,
    next:
      options.revalidateSeconds !== undefined
        ? { revalidate: options.revalidateSeconds }
        : undefined,
  });

  if (!res.ok) {
    throw new ApiError(res.status, await extractErrorMessage(res));
  }

  if (res.status === 204) {
    return undefined as TResponse;
  }

  return (await res.json()) as TResponse;
}
