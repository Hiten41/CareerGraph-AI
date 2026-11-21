import { Network, Compass } from "lucide-react";
export function AuthScreen({
  register,
  setRegister,
  busy,
  error,
  authenticate,
}: {
  register: boolean;
  setRegister: (v: boolean) => void;
  busy: boolean;
  error: string;
  authenticate: (f: FormData) => Promise<void>;
}) {
  return (
    <main className="landing">
      <header className="brand">
        <Network /> CareerGraph <span>AI</span>
      </header>
      <div className="landing-grid">
        <section>
          <p className="kicker">A CLEARER PATH TO WHAT’S NEXT</p>
          <h1>
            Your ambition.
            <br />A better direction.
          </h1>
          <p className="lead">
            Find opportunities that connect to your skills, your interests, and
            the work you want to do.
          </p>
          <div className="pill-row">
            <span>Hybrid search</span>
            <span>Explainable matches</span>
            <span>You control the memory</span>
          </div>
          <div className="landing-note">
            <Compass size={32} />
            <p>
              Built around evidence.
              <br />
              <span>
                See what fits, what’s missing, and what’s still unknown.
              </span>
            </p>
          </div>
          <p className="muted">
            Local demonstration uses clearly labeled fictional jobs. No live
            opportunities or hiring guarantees.
          </p>
        </section>
        <section className="auth-card">
          <p className="eyebrow">YOUR NEXT CHAPTER</p>
          <h2>{register ? "Create your workspace" : "Welcome back"}</h2>
          <p className="muted">
            Start with a profile. Discover the possibilities.
          </p>
          <form action={authenticate}>
            <label>
              Email
              <input name="email" type="email" autoComplete="email" required />
            </label>
            <label>
              Password
              <input
                name="password"
                type="password"
                minLength={12}
                maxLength={128}
                autoComplete={register ? "new-password" : "current-password"}
                required
              />
            </label>
            <button className="primary" disabled={busy}>
              {busy ? "Please wait…" : register ? "Create account" : "Sign in"}
            </button>
          </form>
          {error && (
            <p role="alert" className="error">
              {error}
            </p>
          )}
          <button className="text-btn" onClick={() => setRegister(!register)}>
            {register
              ? "Already have an account? Sign in"
              : "New here? Create an account"}
          </button>
          <p className="fine">
            Resume files are discarded after extraction. Your profile is saved
            only when you confirm.
          </p>
        </section>
      </div>
    </main>
  );
}
