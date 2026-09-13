// Route reserved per frontend/CLAUDE.md's Directory Structure. Full menu
// display is explicitly Phase 2 ("Do NOT Build Yet") — this placeholder
// only makes the route exist/navigable, it does not implement the feature.
import { requireSession } from "@/lib/auth/guards";

interface LocationMenuPageProps {
  params: { id: string };
}

export default async function LocationMenuPage({ params }: LocationMenuPageProps) {
  await requireSession(["owner", "manager"]);

  return (
    <main>
      <h1>Menu — Location {params.id}</h1>
      <p>Phase 2 feature — route reserved, not implemented yet.</p>
    </main>
  );
}
