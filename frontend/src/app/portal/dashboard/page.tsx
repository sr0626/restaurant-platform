// Owner + manager portal dashboard — auth-gated per frontend/CLAUDE.md's
// "Auth-gated portal pages" pattern. Placeholder only (Phase 1 scope:
// "Basic owner portal: edit listing, upload cover photo, set hours" — the
// actual portal UI is not built in this task).
import { requireSession } from "@/lib/auth/guards";

export default async function DashboardPage() {
  const session = await requireSession(["owner", "manager"]);

  return (
    <main>
      <h1>Dashboard</h1>
      <p>Under construction. Signed in as {session.role}.</p>
    </main>
  );
}
