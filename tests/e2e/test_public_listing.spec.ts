// Public pages: homepage, search results, restaurant detail.
//
// No backend is deployed (see playwright.config.ts header comment), so
// these assert the REAL graceful degradation behavior the frontend was
// built with — not fabricated restaurant content. Confirmed by reading:
//   - frontend/src/components/home/PopularNearYou.tsx (homepage grid)
//   - frontend/src/components/search/SearchResults.tsx (search grid)
//   - frontend/src/app/restaurant/[slug]/page.tsx (detail page loader)
import { test, expect } from "@playwright/test";

test.describe("Homepage", () => {
  test("renders hero, search bar, and a graceful empty/error state for the results grid", async ({
    page,
  }) => {
    await page.goto("/");

    // TopBar + Hero render regardless of any API call.
    await expect(page.getByRole("heading", { name: "Discover your taste." })).toBeVisible();
    await expect(page.getByPlaceholder("City, ZIP, or neighborhood")).toBeVisible();
    await expect(page.getByPlaceholder("Cuisine, dish, or restaurant")).toBeVisible();
    await expect(page.getByRole("button", { name: "Search" })).toBeVisible();

    // "Popular near you" — PopularNearYou.tsx catches ANY searchRestaurants()
    // failure (no backend reachable) and renders this InfoPanel. This is
    // real product behavior, not a workaround: see the component's own
    // comment ("Errors are caught and rendered as a friendly empty state,
    // never a broken page").
    await expect(page.getByRole("heading", { name: "Popular near you" })).toBeVisible();
    await expect(
      page.getByText("We can't load restaurants right now")
    ).toBeVisible();
  });

  test("selecting a cuisine chip then searching navigates to /search with the cuisine param", async ({
    page,
  }) => {
    // Chips are plain <button> elements inside a role="group" labeled
    // "Filter by cuisine" (Hero.tsx) — no data-testid exists, so this uses
    // the accessible group + visible text, Playwright's recommended
    // selector strategy when test ids aren't present.
    //
    // On the homepage (Hero.tsx), a chip click only sets local state
    // (`onClick={() => setSelectedCuisine(chip.name)}`) — navigation
    // happens on the Search button's form submit, which reads that state.
    // (Contrast with the search page's own SearchFilterBar.tsx, whose
    // chips DO navigate immediately on click — different component, real
    // difference in behavior, confirmed by reading both files.)
    await page.goto("/");
    const cuisineGroup = page.getByRole("group", { name: "Filter by cuisine" });
    const chip = cuisineGroup.getByRole("button", { name: "North Indian" });
    await chip.click();
    await expect(chip).toHaveAttribute("aria-pressed", "true");

    await page.getByRole("button", { name: "Search" }).click();
    await expect(page).toHaveURL(/\/search\?cuisine=north_indian/);
  });
});

test.describe("Search results page", () => {
  test("renders filter bar and a graceful empty/error state for results", async ({ page }) => {
    await page.goto("/search");

    await expect(page.getByRole("heading", { name: "Search results" })).toBeVisible();
    await expect(page.getByPlaceholder("City, ZIP, or neighborhood")).toBeVisible();

    // SearchResults.tsx: same broad catch-and-degrade behavior as the
    // homepage grid, same InfoPanel copy (shared component).
    await expect(
      page.getByText("We can't load restaurants right now")
    ).toBeVisible();
  });

  test("cuisine filter chip is reflected in the URL and stays selected", async ({ page }) => {
    await page.goto("/search?cuisine=south_indian");
    const filterGroup = page.getByRole("group", { name: "Filter by cuisine" });
    await expect(filterGroup.getByRole("button", { name: "South Indian" })).toHaveAttribute(
      "aria-pressed",
      "true"
    );
  });
});

test.describe("Restaurant detail page", () => {
  // loadRestaurantPageData() (app/restaurant/[slug]/page.tsx) only catches
  // a 404 ApiError from getRestaurantBySlug() and re-throws everything
  // else. With no NEXT_PUBLIC_API_URL configured, apiFetch() throws a 500
  // ApiError immediately (frontend/src/lib/api/client.ts) — not a 404 — so
  // this re-throws and is caught by the App Router error boundary
  // (app/error.tsx) instead of rendering a "not found" page or real
  // content. That is a real, deterministic, honest thing to assert on: it
  // proves the error boundary added in this same wave of work actually
  // renders instead of Next's raw default error screen, for ANY slug,
  // without needing seeded data or a live backend.
  test("shows the graceful error boundary (not raw content, not a crash) for any slug", async ({
    page,
  }) => {
    const response = await page.goto("/restaurant/any-nonexistent-slug");

    // App Router renders error.tsx with a 200 on the client-navigated
    // shell; assert on the rendered content instead of transport status.
    expect(response?.status()).toBeLessThan(500 + 1); // sanity: page responded at all
    // InfoPanel (components/ui/InfoPanel.tsx) renders its title as a
    // styled <p>, not a semantic heading — getByText matches the real DOM
    // instead of assuming a role the markup doesn't have.
    await expect(page.getByText("Something went wrong")).toBeVisible();
    await expect(
      page.getByText("We hit a snag loading this page. Check back shortly, or try again.")
    ).toBeVisible();
    await expect(page.getByRole("button", { name: "Try again" })).toBeVisible();

    // TopBar still renders inside the error boundary (error.tsx renders it
    // explicitly) — confirms this is the branded boundary, not a raw crash.
    await expect(page.getByText("Swarasa")).toBeVisible();
  });

  // schema.org JSON-LD (frontend/src/app/restaurant/[slug]/page.tsx's
  // buildRestaurantSchema()) is only emitted on the success path, AFTER
  // loadRestaurantPageData() resolves — see the <script type=
  // "application/ld+json"> right above <main> in that file. Today, every
  // request for every slug throws before reaching that point (see the test
  // above), so the JSON-LD script is never rendered at all — not "renders
  // with placeholder/empty data," genuinely absent from the DOM. This is
  // required by tests/CLAUDE.md's Phase 1 checklist ("All public listing
  // pages render with schema.org JSON-LD") and cannot be honestly asserted
  // as passing right now.
  //
  // Unblocks when: a live backend (local FastAPI is enough, doesn't need
  // to be the deployed Lambda) is reachable at NEXT_PUBLIC_API_URL and has
  // at least one seeded restaurant_brand + restaurant_location, so
  // loadRestaurantPageData() can resolve successfully for a real slug.
  test.fixme(
    "restaurant detail page includes schema.org Restaurant JSON-LD",
    async ({ page }) => {
      await page.goto("/restaurant/some-seeded-slug");
      const jsonLd = page.locator('script[type="application/ld+json"]');
      await expect(jsonLd).toHaveCount(1);
      const payload = JSON.parse((await jsonLd.textContent()) ?? "{}");
      expect(payload["@type"]).toBe("Restaurant");
      expect(payload.name).toBeTruthy();
    }
  );
});
