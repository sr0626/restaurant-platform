// Admin claim review queue — auth-gated (admin only). Implements
// docs/DECISIONS.md "Claim flow" queue at the routing level only;
// placeholder UI, real review UI is out of this task's scope.
import { requireSession } from "@/lib/auth/guards";

export default async function AdminClaimsPage() {
  await requireSession(["admin"]);

  return (
    <main>
      <h1>Claims Queue</h1>
      <p>Under construction — admin claim review queue.</p>
    </main>
  );
}
