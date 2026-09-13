// Route reserved per frontend/CLAUDE.md's Directory Structure. Deals
// feed/deal cards are explicitly Phase 2 ("Do NOT Build Yet") — this
// placeholder only makes the route exist/navigable, it does not implement
// the feature.
import { requireSession } from "@/lib/auth/guards";

interface LocationDealsPageProps {
  params: { id: string };
}

export default async function LocationDealsPage({ params }: LocationDealsPageProps) {
  await requireSession(["owner", "manager"]);

  return (
    <main>
      <h1>Deals — Location {params.id}</h1>
      <p>Phase 2 feature — route reserved, not implemented yet.</p>
    </main>
  );
}
