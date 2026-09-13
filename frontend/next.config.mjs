/**
 * Base Next.js config — plumbing only, no visual/theme decisions here.
 *
 * next/image `remotePatterns` for restaurant photos (served from
 * CloudFront — root CLAUDE.md "Media: S3 + CloudFront") are intentionally
 * NOT configured yet: frontend/CLAUDE.md's Environment Variables list has
 * no NEXT_PUBLIC_ var for the CloudFront domain today. Add the env var and
 * the matching remotePattern together once Infra provisions the
 * distribution — hardcoding a guessed domain now would violate root
 * CLAUDE.md's "AWS Best Practices" (never hardcode infra endpoints).
 *
 * Plain JS (not next.config.ts): TS-format config needs Next 15+; this
 * project is pinned to Next 14.2.18 (root CLAUDE.md stack decision).
 *
 * @type {import('next').NextConfig}
 */
const nextConfig = {
  reactStrictMode: true,
};

export default nextConfig;
