"use client";
import { EvidenceValue } from "../components/evidence-value";
import { AuthScreen } from "../features/auth-screen";
import { MatchDialog } from "../features/match-dialog";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import {
  Compass,
  Search,
  Bookmark,
  UserRound,
  SlidersHorizontal,
  ChartNoAxesCombined,
  Database,
  Sun,
  Moon,
  Send,
  Network,
  LogOut,
  Plus,
  FileText,
} from "lucide-react";
import { api, body, setCsrf } from "../lib/api";
import type { Profile, Result, Chat, Job, Evaluation } from "../types/domain";
import { JobCard } from "../components/job-card";
type User = {
  provider_consent: boolean;
  id: string;
  email: string;
  role: string;
  csrf: string;
};
const emptyProfile: Profile = {
  name: "",
  skills: [],
  graduation_year: null,
  experience_years: null,
  projects: [],
  education: [],
  languages: [],
  evidence: {},
};
const nav = [
  ["discover", "Discover", Compass],
  ["profile", "Your profile", UserRound],
  ["saved", "Saved opportunities", Bookmark],
  ["preferences", "Preferences & memory", SlidersHorizontal],
  ["analytics", "Evaluation lab", ChartNoAxesCombined],
  ["admin", "Data sources", Database],
] as const;
export default function Home() {
  const [user, setUser] = useState<User | null>(null),
    [view, setView] = useState("discover"),
    [checking, setChecking] = useState(true),
    [register, setRegister] = useState(false),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [notice, setNotice] = useState(""),
    [dark, setDark] = useState(false);
  const [profile, setProfile] = useState<Profile>(emptyProfile),
    [query, setQuery] = useState(""),
    [results, setResults] = useState<Result[]>([]),
    [chat, setChat] = useState<Chat | null>(null),
    [session, setSession] = useState(""),
    [preferences, setPreferences] = useState(""),
    [saved, setSaved] = useState<Job[]>([]),
    [evaluations, setEvaluations] = useState<Evaluation[]>([]),
    [runs, setRuns] = useState<unknown[]>([]),
    [selected, setSelected] = useState<Result | null>(null),
    [strategy, setStrategy] = useState("personalized");
  const [hostedResume, setHostedResume] = useState(false);
  const dialog = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    api<User>("/auth/me")
      .then((u) => {
        setCsrf(u.csrf);
        setUser(u);
      })
      .catch(() => {})
      .finally(() => setChecking(false));
  }, []);
  async function action(fn: () => Promise<void>) {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await fn();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Request failed");
    } finally {
      setBusy(false);
    }
  }
  async function navigate(next: string) {
    setView(next);
    await action(async () => {
      if (next === "profile") {
        const p = await api<{ profile: Profile }>("/profile");
        setProfile({ ...emptyProfile, ...p.profile });
      }
      if (next === "preferences")
        setPreferences(
          (
            await api<{ preferences: string[] }>("/preferences")
          ).preferences.join("\n"),
        );
      if (next === "saved") setSaved(await api<Job[]>("/saved-jobs"));
      if (next === "analytics")
        setEvaluations(await api<Evaluation[]>("/evaluations"));
      if (next === "admin") setRuns(await api<unknown[]>("/admin/ingestion"));
    });
  }
  async function authenticate(form: FormData) {
    await action(async () => {
      const data = await api<{ csrf: string }>(
        register ? "/auth/register" : "/auth/login",
        {
          method: "POST",
          body: body({
            email: form.get("email"),
            password: form.get("password"),
          }),
        },
      );
      setCsrf(data.csrf);
      setUser(await api<User>("/auth/me"));
    });
  }
  async function discover(conversation: boolean) {
    if (!query.trim()) return;
    setResults([]);
    setChat(null);
    await action(async () => {
      if (conversation) {
        const id =
          session ||
          (await api<{ id: string }>("/chat/sessions", { method: "POST" })).id;
        setSession(id);
        const response = await api<Chat>(`/chat/sessions/${id}/messages`, {
          method: "POST",
          body: body({
            message: query,
            allow_provider: user?.provider_consent === true,
          }),
        });
        setChat(response);
        if (response.tools.includes("search_jobs"))
          setResults(response.results);
        setQuery("");
      } else {
        setResults(
          (
            await api<{ results: Result[] }>("/jobs/search", {
              method: "POST",
              body: body({ query, strategy }),
            })
          ).results,
        );
        setChat(null);
      }
    });
  }
  function open(result: Result) {
    setSelected(result);
    dialog.current?.showModal();
  }
  if (checking)
    return (
      <main className="welcome">
        <p role="status">Opening your workspace…</p>
      </main>
    );
  if (!user)
    return (
      <AuthScreen {...{ register, setRegister, busy, error, authenticate }} />
    );
  return (
    <div className={dark ? "workspace dark" : "workspace"}>
      <aside className="sidebar">
        <Link href="/" className="brand">
          <Network /> CareerGraph <span>AI</span>
        </Link>
        <p className="nav-label">YOUR WORKSPACE</p>
        <nav>
          {nav
            .filter(([key]) => key !== "admin" || user.role === "admin")
            .map(([key, label, Icon]) => (
              <button
                key={key}
                className={view === key ? "nav-item active" : "nav-item"}
                onClick={() => navigate(key)}
              >
                <Icon size={19} />
                {label}
              </button>
            ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="demo-badge">SYNTHETIC DATA ENVIRONMENT</div>
          <p>
            Explore the product.
            <br />
            Listings are fictional.
          </p>
          <button className="nav-item" onClick={() => setDark(!dark)}>
            {dark ? <Sun size={18} /> : <Moon size={18} />}{" "}
            {dark ? "Light" : "Dark"} appearance
          </button>
          <button
            className="nav-item"
            onClick={() =>
              action(async () => {
                await api("/auth/logout", { method: "POST" });
                setUser(null);
                setSession("");
                setResults([]);
                setChat(null);
              })
            }
          >
            <LogOut size={18} />
            Sign out
          </button>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <span>
            Workspace <span className="slash">/</span>{" "}
            {nav.find((n) => n[0] === view)?.[1]}
          </span>
          <span className="account">
            <span className="avatar">{user.email[0].toUpperCase()}</span>
            {user.email}
          </span>
        </header>
        <main className="content">
          {error && (
            <div role="alert" className="error">
              {error}
            </div>
          )}
          {notice && (
            <div role="status" className="notice">
              {notice}
            </div>
          )}
          {busy && (
            <p role="status" className="loading">
              Working with your data…
            </p>
          )}
          {view === "discover" && (
            <>
              <div className="page-heading">
                <div>
                  <p className="kicker">CONNECT YOUR POTENTIAL</p>
                  <h1>Find your next direction.</h1>
                  <p className="muted">
                    A thoughtful search, built around you.
                  </p>
                </div>
                <span className="outline-badge">Evidence over guesswork</span>
              </div>
              <section className="search-panel">
                <div className="search-heading">
                  <span className="spark">
                    <Compass size={22} />
                  </span>
                  <div>
                    <h2>What would you like to work on?</h2>
                    <p>Describe the role. Refine it together.</p>
                  </div>
                </div>
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    discover(true);
                  }}
                >
                  <label className="sr-only" htmlFor="query">
                    Describe your job search or follow-up
                  </label>
                  <textarea
                    id="query"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Find remote Python internships for 2028 graduates…"
                    rows={2}
                    maxLength={1000}
                  />
                  <div className="search-actions">
                    <label>
                      Direct search strategy
                      <select
                        value={strategy}
                        onChange={(e) => setStrategy(e.target.value)}
                      >
                        <option value="personalized">
                          Personalized hybrid
                        </option>
                        <option value="hybrid">Hybrid</option>
                        <option value="keyword">Keyword</option>
                        <option value="semantic">Semantic</option>
                      </select>
                    </label>
                    <button
                      type="button"
                      className="secondary"
                      disabled={busy || !query.trim()}
                      onClick={() => discover(false)}
                    >
                      <Search size={16} />
                      Direct search
                    </button>
                    <button
                      className="primary"
                      disabled={busy || !query.trim()}
                    >
                      <Send size={16} />
                      Ask agent
                    </button>
                  </div>
                </form>
                <label>
                  <span>
                    <input
                      type="checkbox"
                      checked={user.provider_consent}
                      onChange={(e) => {
                        const allowed = e.target.checked;
                        action(async () => {
                          await api("/privacy/provider-consent", {
                            method: "PUT",
                            body: body({ allowed }),
                          });
                          setUser({ ...user, provider_consent: allowed });
                        });
                      }}
                    />{" "}
                    Allow the configured AI provider to process this chat,
                    profile and job evidence.
                  </span>
                </label>
                <div className="suggestions">
                  {[
                    "Remote Python internships",
                    "AI/ML internships for 2028 graduates",
                    "Backend engineering internships",
                  ].map((q) => (
                    <button key={q} onClick={() => setQuery("Find " + q)}>
                      {q}
                    </button>
                  ))}
                </div>
              </section>
              {chat && (
                <section className="agent-panel">
                  <div className="section-heading">
                    <h3>{chat.mode}</h3>
                    <button
                      className="text-btn"
                      onClick={() => {
                        setSession("");
                        setChat(null);
                        setResults([]);
                      }}
                    >
                      <Plus size={15} />
                      New conversation
                    </button>
                  </div>
                  <p>{chat.message}</p>
                  {chat.pending_preference && (
                    <p>
                      Proposed: <strong>{chat.pending_preference}</strong>{" "}
                      <button
                        className="secondary"
                        onClick={() => setQuery("confirm")}
                      >
                        Review & confirm
                      </button>
                    </p>
                  )}
                  <div className="tags">
                    {Object.entries(chat.constraints)
                      .filter(([, v]) => v !== null)
                      .map(([k, v]) => (
                        <span key={k}>
                          {k.replaceAll("_", " ")}: {String(v)}
                        </span>
                      ))}
                  </div>
                  <p className="fine">
                    Tools invoked: {chat.tools.join(" · ") || "None"}
                  </p>
                  <details>
                    <summary>View grounded tool evidence</summary>
                    <EvidenceValue value={chat.evidence} />
                  </details>
                </section>
              )}
              <div className="section-heading">
                <h2>
                  {results.length
                    ? "Your recommendations"
                    : "Your next opportunity starts here"}
                </h2>
                <span className="muted">
                  {results.length
                    ? `${results.length} results · relevance, not hiring probability`
                    : "Search to build your shortlist"}
                </span>
              </div>
              {results.length ? (
                <div className="results">
                  {results.map((r) => (
                    <JobCard
                      key={r.job.id}
                      result={r}
                      onOpen={() => open(r)}
                      onSave={() =>
                        action(async () => {
                          await api("/saved-jobs", {
                            method: "POST",
                            body: body({ job_id: r.job.id }),
                          });
                          setNotice("Saved to your opportunities.");
                        })
                      }
                      onDismiss={() =>
                        action(async () => {
                          await api("/feedback", {
                            method: "POST",
                            body: body({ job_id: r.job.id, value: -1 }),
                          });
                          setResults(
                            results.filter((x) => x.job.id !== r.job.id),
                          );
                          setNotice("Feedback saved for future ranking.");
                        })
                      }
                    />
                  ))}
                </div>
              ) : (
                <div className="empty">
                  <Network size={44} />
                  <h3>More than a list of jobs.</h3>
                  <p>
                    Search across skills and meaning. Every recommendation shows
                    <br />
                    the requirements you match and the information we can’t
                    verify.
                  </p>
                  <button
                    className="secondary"
                    onClick={() => navigate("profile")}
                  >
                    Build your profile
                  </button>
                </div>
              )}
            </>
          )}
          {view === "profile" && (
            <>
              <p className="kicker">YOUR FOUNDATION</p>
              <h1>A profile you control.</h1>
              <p className="muted">
                Review extracted details before saving. Completeness reflects
                filled fields, never employability.
              </p>
              <section className="panel">
                {user.provider_consent && (
                  <label>
                    <span>
                      <input
                        type="checkbox"
                        checked={hostedResume}
                        onChange={(e) => setHostedResume(e.target.checked)}
                      />{" "}
                      Send text from this PDF to the configured provider for
                      excerpt selection.
                    </span>
                  </label>
                )}
                <label className="upload">
                  <FileText />
                  <strong>Import a PDF resume</strong>
                  <span>
                    Text PDFs only · up to 5 MB · original file never retained
                  </span>
                  <input
                    type="file"
                    accept="application/pdf"
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file)
                        action(async () => {
                          const form = new FormData();
                          form.append("file", file);
                          const parsed = await api<{ profile: Profile }>(
                            "/profile/resume" +
                              (hostedResume && user.provider_consent
                                ? "?hosted=true"
                                : ""),
                            { method: "POST", body: form },
                          );
                          setProfile({ ...emptyProfile, ...parsed.profile });
                          setNotice(
                            "Extracted draft. Review and save your profile.",
                          );
                        });
                    }}
                  />
                </label>
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    action(async () => {
                      await api("/profile", {
                        method: "PUT",
                        body: body(profile),
                      });
                      setNotice("Profile saved.");
                    });
                  }}
                >
                  <div className="form-grid">
                    <label>
                      Name
                      <input
                        value={profile.name}
                        onChange={(e) =>
                          setProfile({ ...profile, name: e.target.value })
                        }
                      />
                    </label>
                    <label>
                      Graduation year
                      <input
                        type="number"
                        min={1950}
                        max={2100}
                        value={profile.graduation_year ?? ""}
                        onChange={(e) =>
                          setProfile({
                            ...profile,
                            graduation_year: e.target.value
                              ? Number(e.target.value)
                              : null,
                          })
                        }
                      />
                    </label>
                    <label>
                      Experience (years)
                      <input
                        type="number"
                        min={0}
                        max={80}
                        step="0.5"
                        value={profile.experience_years ?? ""}
                        onChange={(e) =>
                          setProfile({
                            ...profile,
                            experience_years: e.target.value
                              ? Number(e.target.value)
                              : null,
                          })
                        }
                      />
                    </label>
                    <label>
                      Skills (comma separated)
                      <input
                        value={profile.skills.join(", ")}
                        onChange={(e) =>
                          setProfile({
                            ...profile,
                            skills: e.target.value
                              .split(",")
                              .map((s) => s.trim()),
                          })
                        }
                      />
                    </label>
                    {(
                      [
                        "education",
                        "projects",
                        "languages",
                        "experience",
                      ] as const
                    ).map((key) => (
                      <label key={key}>
                        {key}
                        <textarea
                          value={(profile[key] || []).join("\n")}
                          onChange={(e) =>
                            setProfile({
                              ...profile,
                              [key]: e.target.value.split("\n"),
                            })
                          }
                        />
                      </label>
                    ))}
                  </div>
                  <p className="muted">
                    {Math.round(
                      ([
                        "name",
                        "skills",
                        "education",
                        "projects",
                        "graduation_year",
                      ].filter((k) => {
                        const v = profile[k as keyof Profile];
                        return Array.isArray(v) ? v.some(Boolean) : Boolean(v);
                      }).length /
                        5) *
                        100,
                    )}
                    % profile completeness
                  </p>
                  <button className="primary" disabled={busy}>
                    Confirm & save profile
                  </button>
                </form>
              </section>
            </>
          )}
          {view === "saved" && (
            <>
              <h1>Your shortlist.</h1>
              <p className="muted">Opportunities you want to revisit.</p>
              {saved.length ? (
                saved.map((j) => (
                  <section className="panel" key={j.id}>
                    <h2>{j.title}</h2>
                    <p>
                      {j.company} · {j.location} ·{" "}
                      {j.synthetic ? "Fictional demo" : "Imported source"}
                    </p>
                    <p>{j.description}</p>
                    <button
                      className="secondary"
                      onClick={() =>
                        action(async () => {
                          await api("/saved-jobs/" + j.id, {
                            method: "DELETE",
                          });
                          setSaved(saved.filter((x) => x.id !== j.id));
                        })
                      }
                    >
                      Remove from saved
                    </button>
                  </section>
                ))
              ) : (
                <div className="empty">
                  <Bookmark size={36} />
                  <h2>No saved opportunities yet.</h2>
                  <p>Save a result from discovery to keep it here.</p>
                </div>
              )}
            </>
          )}
          {view === "preferences" && (
            <>
              <h1>Your preferences. Your memory.</h1>
              <p className="muted">
                Only explicitly saved preferences influence future ranking.
              </p>
              <form
                className="panel"
                onSubmit={(e) => {
                  e.preventDefault();
                  action(async () => {
                    await api("/preferences", {
                      method: "PUT",
                      body: body({
                        preferences: preferences
                          .split("\n")
                          .map((s) => s.trim())
                          .filter(Boolean),
                      }),
                    });
                    setNotice("Preferences updated.");
                  });
                }}
              >
                <label>
                  Role and technical interests (one per line)
                  <textarea
                    rows={7}
                    value={preferences}
                    onChange={(e) => setPreferences(e.target.value)}
                    placeholder="backend\nretrieval\nsearch engineering"
                  />
                </label>
                <button className="primary" disabled={busy}>
                  Save preferences
                </button>
              </form>
              <section className="panel">
                <h2>Delete your data</h2>
                <p>
                  Removes your account, profile, sessions, feedback, and saved
                  jobs. This cannot be undone.
                </p>
                <button
                  className="danger"
                  onClick={() => {
                    if (
                      window.confirm(
                        "Permanently delete your CareerGraph account and all private data?",
                      )
                    )
                      action(async () => {
                        await api("/auth/me", { method: "DELETE" });
                        setUser(null);
                        setResults([]);
                        setChat(null);
                      });
                  }}
                >
                  Delete account and data
                </button>
              </section>
            </>
          )}
          {view === "analytics" && (
            <>
              <p className="kicker">MEASURE, THEN IMPROVE</p>
              <h1>Evaluation lab.</h1>
              <p className="muted">
                Actual stored runs. Synthetic relevance judgments are
                diagnostic, not evidence of hiring effectiveness.
              </p>
              {evaluations.length ? (
                evaluations.map((run) => (
                  <section className="panel" key={run.id}>
                    <h2>Run · {new Date(run.created_at).toLocaleString()}</h2>
                    <EvidenceValue value={run.metadata} />
                    <div className="metric-grid">
                      {Object.entries(run.metrics).map(([name, value]) => (
                        <div className="metric" key={name}>
                          <p>{name.replaceAll("_", " ")}</p>
                          <div>
                            {typeof value === "number" ? (
                              value.toFixed(3)
                            ) : typeof value === "string" ? (
                              value
                            ) : (
                              <EvidenceValue value={value} />
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </section>
                ))
              ) : (
                <div className="empty">
                  <ChartNoAxesCombined size={42} />
                  <h2>No evaluations have run yet.</h2>
                  <p>
                    Run the evaluation script against the seeded database.
                    <br />
                    Metrics appear here only after a real run completes.
                  </p>
                </div>
              )}
            </>
          )}
          {view === "admin" && (
            <>
              <h1>Data sources.</h1>
              <p className="muted">
                Admin-only validated JSON ingestion. Records must have
                authorized provenance.
              </p>
              <section className="panel">
                <label>
                  Import job JSON
                  <input
                    type="file"
                    accept=".json"
                    onChange={(e) => {
                      const f = e.target.files?.[0];
                      if (f)
                        action(async () => {
                          await api("/admin/ingestion", {
                            method: "POST",
                            body: await f.text(),
                          });
                          setNotice(
                            "Import processed. See the ingestion history for details.",
                          );
                          setRuns(await api<unknown[]>("/admin/ingestion"));
                        });
                    }}
                  />
                </label>
                <h2>Ingestion history</h2>
                <EvidenceValue value={runs} />
              </section>
            </>
          )}
        </main>
        <footer>
          CareerGraph AI{" "}
          <span>
            Built by <a href="https://github.com/Hiten41">Hiten Arora</a>
          </span>
        </footer>
      </div>
      <MatchDialog {...{ selected, dialog }} />
    </div>
  );
}
