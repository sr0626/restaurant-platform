// Homepage / search entry point. Deliberately unstyled — the homepage
// visual/color direction is still under review (5 candidate designs on
// the design canvas, not yet picked). This placeholder exists only so the
// route is navigable; do not add layout/visual decisions here yet.
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Indian Restaurant Discovery — Dallas-Fort Worth",
  description:
    "Find verified Indian restaurants across Dallas-Fort Worth, filter by regional cuisine and dietary needs.",
};

export default function HomePage() {
  return (
    <main>
      <h1>Indian Restaurant Discovery — Dallas-Fort Worth</h1>
      <p>Under construction — homepage design is pending the color/style direction decision.</p>
    </main>
  );
}
