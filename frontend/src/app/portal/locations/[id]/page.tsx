// Owner/manager location editor — auth-gated. Phase 1 scope covers edit
// listing, cover photo upload, and hours; placeholder only in this task.
import { requireSession } from "@/lib/auth/guards";

interface LocationPageProps {
  params: { id: string };
}

export default async function PortalLocationPage({ params }: LocationPageProps) {
  await requireSession(["owner", "manager"]);

  return (
    <main>
      <h1>Location {params.id}</h1>
      <p>Under construction — edit listing, cover photo, and hours (Phase 1 scope).</p>
    </main>
  );
}
