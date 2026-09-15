// Site-wide public origin, used for absolute URLs in SEO surfaces that
// require them (sitemap.xml entries, metadataBase for resolving relative
// `alternates.canonical` paths like `/restaurant/{slug}` — see
// frontend/CLAUDE.md "SEO Requirements", "Canonical URLs on all pages").
//
// No production domain is finalized yet (docs/DECISIONS.md: "swarasa.com"
// is taken, a modifier domain such as "findswarasa.com" is the working
// plan) — same "never hardcode, always read from an env var" posture as
// `lib/auth/config.ts` for Cognito. Falls back to the Amplify default
// domain pattern so local/preview builds still produce well-formed
// (if not yet final) absolute URLs instead of throwing; set
// NEXT_PUBLIC_SITE_URL in the real environment once the domain lands.
const FALLBACK_SITE_URL = "https://www.swarasa.com";

export const SITE_URL: string = (process.env.NEXT_PUBLIC_SITE_URL ?? FALLBACK_SITE_URL).replace(
  /\/+$/,
  ""
);
