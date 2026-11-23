import { Network, ArrowUpRight, ArrowRight, Check } from "lucide-react";
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
    <main className="entry">
      <section className="entry-story">
        <header>
          <Network aria-hidden="true" /> CareerGraph AI
        </header>
        <div className="entry-intro">
          <h1>
            Find work that <em>fits you.</em>
          </h1>
          <p>
            Explore roles by skill, then see the evidence behind each match.
          </p>
          <figure className="entry-example">
            <figcaption>
              Example match <ArrowUpRight aria-hidden="true" size={18} />
            </figcaption>
            <strong>Backend Engineering Intern</strong>
            <p>
              <Check aria-hidden="true" size={16} /> Skill overlap{" "}
              <b>Python · SQL</b>
            </p>
            <small>Illustration from a fictional job search</small>
          </figure>
        </div>
        <footer>Built by Hiten Arora</footer>
      </section>
      <section className="entry-account">
        <div className="entry-form">
          <h2>{register ? "Create your account" : "Welcome back"}</h2>
          <p>
            {register
              ? "Create a profile to start exploring roles."
              : "Sign in to your CareerGraph workspace."}
          </p>
          <form action={authenticate}>
            <label>
              Email
              <input
                placeholder="you@example.com"
                name="email"
                type="email"
                autoComplete="email"
                required
              />
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
            {register && (
              <small>Use at least 12 characters for your password.</small>
            )}
            <button className="primary" disabled={busy}>
              {busy ? "Please wait…" : register ? "Create account" : "Sign in"}{" "}
              <ArrowRight size={18} aria-hidden="true" />
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
        </div>
      </section>
    </main>
  );
}
