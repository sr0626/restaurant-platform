// Admin listings management — auth-gated (admin only). Placeholder UI.
import { requireSession } from "@/lib/auth/guards";

export default async function AdminListingsPage() {
  await requireSession(["admin"]);

  return (
    <main>
      <h1>Listings</h1>
      <p>Under construction — admin listings management.</p>
    </main>
  );
}
