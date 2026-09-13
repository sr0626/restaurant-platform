// Public restaurant listing page — SSR + schema.org JSON-LD, per
// frontend/CLAUDE.md's "SSR listing page (SEO critical)" and "schema.org
// Restaurant markup (required on every listing page)" Key Patterns.
//
// The visual layout below is intentionally a bare placeholder (pending the
// homepage/search color/style decision) — but the SEO plumbing (SSR,
// generateMetadata, JSON-LD, canonical, 404 handling) is real, since none
// of that depends on a visual direction.
//
// FLAGGED JUDGMENT CALL (see final report): frontend/CLAUDE.md's example
// schema builds address/telephone/openingHours straight off the fetched
// restaurant, but docs/API_CONTRACTS.md splits that data across
// restaurant_brand (name, description, cuisine_tags) and
// restaurant_location (address, phone, hours). This page fetches the
// brand by slug, then its first/primary location, and merges both into
// the JSON-LD — a brand with zero locations yet renders schema without an
// address rather than failing.
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { ApiError } from "@/lib/api/client";
import { getRestaurantBySlug, getRestaurantLocations } from "@/lib/api/restaurants";
import type { LocationSummary } from "@/types/location";
import type { RestaurantBrand } from "@/types/restaurant";

interface RestaurantPageProps {
  params: { slug: string };
}

interface RestaurantPageData {
  restaurant: RestaurantBrand;
  primaryLocation: LocationSummary | null;
}

async function loadRestaurantPageData(slug: string): Promise<RestaurantPageData | null> {
  let restaurant: RestaurantBrand;
  try {
    restaurant = await getRestaurantBySlug(slug);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      return null;
    }
    throw error;
  }

  const locations = await getRestaurantLocations(restaurant.id, { page: 1, page_size: 1 });
  return { restaurant, primaryLocation: locations.results[0] ?? null };
}

export async function generateMetadata({ params }: RestaurantPageProps): Promise<Metadata> {
  const data = await loadRestaurantPageData(params.slug);
  if (!data) {
    return { title: "Restaurant Not Found" };
  }
  const { restaurant, primaryLocation } = data;

  // frontend/CLAUDE.md SEO Requirements meta title format:
  // "{Restaurant Name} — Indian Restaurant in {City}, {State}"
  const cityState = primaryLocation ? ` in ${primaryLocation.city}, ${primaryLocation.state}` : "";

  return {
    title: `${restaurant.name} — Indian Restaurant${cityState}`,
    // "first 150 chars of restaurant `about` field" — description here is
    // the closest documented equivalent (no separate `about` field on
    // RestaurantBrand per docs/API_CONTRACTS.md).
    description: restaurant.description.slice(0, 150),
    alternates: {
      canonical: `/restaurant/${restaurant.slug}`,
    },
  };
}

function buildRestaurantSchema(restaurant: RestaurantBrand, location: LocationSummary | null) {
  return {
    "@context": "https://schema.org",
    "@type": "Restaurant",
    name: restaurant.name,
    servesCuisine: restaurant.cuisine_tags.map((tag) => tag.display_name),
    ...(location
      ? {
          address: {
            "@type": "PostalAddress",
            streetAddress: location.address_line1,
            addressLocality: location.city,
            addressRegion: location.state,
            postalCode: location.postal_code,
          },
          telephone: location.phone,
        }
      : {}),
  };
}

export default async function RestaurantPage({ params }: RestaurantPageProps) {
  const data = await loadRestaurantPageData(params.slug);
  if (!data) {
    notFound();
  }
  const { restaurant, primaryLocation } = data;

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(buildRestaurantSchema(restaurant, primaryLocation)),
        }}
      />
      <main>
        <h1>{restaurant.name}</h1>
        {!restaurant.is_claimed && <p>Unclaimed listing — claim this listing.</p>}
        <p>Under construction — full listing page is pending the homepage/search visual design decision.</p>
      </main>
    </>
  );
}
