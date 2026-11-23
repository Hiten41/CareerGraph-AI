import { Waypoints, ArrowUpRight, ArrowRight, Check } from "lucide-react";
import { useState } from "react";
import { api, body } from "../lib/api";
export function AuthScreen({
  dark,
  register,
  setRegister,
  busy,
  error,
  authenticate,
}: {
  dark: boolean;
  register: boolean;
  setRegister: (v: boolean) => void;
  busy: boolean;
  error: string;
  authenticate: (f: FormData) => Promise<void>;
}) {
  const [reset, setReset] = useState(false),
    [status, setStatus] = useState(""),
    [resetting, setResetting] = useState(false);
  async function recover(form: FormData) {
    setResetting(true);
    try {
      await api("/auth/reset-password", {
        method: "POST",
        body: body({
          email: form.get("email"),
          password: form.get("password"),
          code: String(form.get("code")).trim(),
        }),
      });
      setReset(false);
      setStatus(
        "Password updated. Sign in with your new password. Generate a new recovery code in Preferences & memory.",
      );
    } catch (e) {
      setStatus(e instanceof Error ? e.message : "Unable to reset password.");
    } finally {
      setResetting(false);
    }
  }
  return (
    <main className={dark ? "entry dark" : "entry"}>
      <section className="entry-story">
        <header>
          <Waypoints aria-hidden="true" /> CareerGraph AI
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
          <h2>
            {reset
              ? "Reset your password"
              : register
                ? "Create your account"
                : "Welcome back"}
          </h2>
          <p>
            {reset
              ? "Enter the recovery code saved from your account."
              : register
                ? "Create a profile to start exploring roles."
                : "Sign in to your CareerGraph workspace."}
          </p>
          <form
            key={reset ? "reset" : "auth"}
            action={reset ? recover : authenticate}
          >
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
            {reset && (
              <label>
                Recovery code
                <input name="code" required autoComplete="off" />
              </label>
            )}
            <label>
              {reset ? "New password" : "Password"}
              <input
                name="password"
                type="password"
                minLength={12}
                maxLength={128}
                autoComplete={
                  register || reset ? "new-password" : "current-password"
                }
                required
              />
            </label>
            {(register || reset) && (
              <small>Use at least 12 characters for your password.</small>
            )}
            <button className="primary" disabled={busy || resetting}>
              {busy || resetting
                ? "Please wait…"
                : reset
                  ? "Reset password"
                  : register
                    ? "Create account"
                    : "Sign in"}{" "}
              <ArrowRight size={18} aria-hidden="true" />
            </button>
          </form>
          {status && <p role="status">{status}</p>}
          {!reset && error && (
            <p role="alert" className="error">
              {error}
            </p>
          )}
          {!register && (
            <button
              className="text-btn"
              onClick={() => {
                setReset(!reset);
                setStatus("");
              }}
            >
              {reset ? "Back to sign in" : "Forgot password?"}
            </button>
          )}
          {!reset && (
            <button
              className="text-btn"
              onClick={() => {
                setStatus("");
                setRegister(!register);
              }}
            >
              {register
                ? "Already have an account? Sign in"
                : "New here? Create an account"}
            </button>
          )}
          <p className="fine">
            Resume files are discarded after extraction. Your profile is saved
            only when you confirm.
          </p>
        </div>
      </section>
    </main>
  );
}
