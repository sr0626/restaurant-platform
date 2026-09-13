// JUDGMENT CALL (flagged in final report): not one of the paths explicitly
// listed in frontend/CLAUDE.md's Directory Structure, but every auth-gated
// portal/admin placeholder below redirects here on no/invalid session
// (frontend/CLAUDE.md's own "Auth-gated portal pages" pattern), so the
// route has to exist for the app to be navigable. The actual Cognito
// Hosted UI / sign-in flow is out of this task's scope (auth scaffolding
// only, no portal UI) — this is a bare placeholder.
export default function LoginPage() {
  return (
    <main>
      <h1>Sign In</h1>
      <p>Under construction — Cognito sign-in flow not yet built.</p>
    </main>
  );
}
