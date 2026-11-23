import { useState } from "react";
import { BookmarkCheck, Columns2 } from "lucide-react";
import type { Result, Job } from "../types/domain";
import { api, body } from "../lib/api";
export function SavedList({
  jobs,
  evidence,
  open,
  remove,
  action,
}: {
  jobs: Job[];
  evidence: Record<string, Result | null>;
  open: (r: Result) => void;
  remove: (id: string) => Promise<void>;
  action: (work: () => Promise<void>) => Promise<void>;
}) {
  const [chosen, setChosen] = useState<string[]>([]);
  const [comparison, setComparison] = useState<
    Pick<Result, "job" | "explanation">[]
  >([]);
  return (
    <>
      <div className="section-heading">
        <span>{jobs.length} saved</span>
        {jobs.length >= 2 && (
          <button
            className="secondary"
            disabled={chosen.length !== 2}
            onClick={() =>
              action(async () =>
                setComparison(
                  await api("/jobs/compare", {
                    method: "POST",
                    body: body({ job_ids: chosen }),
                  }),
                ),
              )
            }
          >
            <Columns2 size={16} />
            Compare selected ({chosen.length}/2)
          </button>
        )}
      </div>
      {comparison.length > 0 && (
        <section className="panel">
          <h2>Skill comparison</h2>
          <div className="results">
            {comparison.map((r) => (
              <div key={r.job.id}>
                <h3>{r.job.title}</h3>
                <p>{r.job.company}</p>
                <p>
                  Matched: {r.explanation.matched.join(", ") || "None verified"}
                </p>
                <p>
                  Missing:{" "}
                  {r.explanation.missing.join(", ") || "None identified"}
                </p>
              </div>
            ))}
          </div>
        </section>
      )}
      <div className="results">
        {jobs.map((job) => {
          const r = evidence[job.id];
          return (
            <article key={job.id} className="job-card">
              <div className="card-top">
                <span className="company-icon">
                  <BookmarkCheck size={20} />
                </span>
                <div>
                  <p className="eyebrow">{job.company}</p>
                  <h2>{job.title}</h2>
                </div>
              </div>
              <p className="muted">
                {[job.location, job.mode, job.employment]
                  .filter(Boolean)
                  .join(" · ")}
              </p>
              {r && (
                <p className="match">
                  {r.eligibility === "eligible"
                    ? "Meets search filters"
                    : r.eligibility === "historical_unknown"
                      ? "Original filters unavailable"
                      : "Some filters unverified"}{" "}
                  · {r.explanation.matched.length} matching skills
                </p>
              )}
              <p>{job.description}</p>
              <small>
                {job.synthetic ? "Fictional demo listing" : "Imported listing"}
              </small>
              {jobs.length >= 2 && (
                <label>
                  <span>
                    <input
                      type="checkbox"
                      checked={chosen.includes(job.id)}
                      disabled={!chosen.includes(job.id) && chosen.length === 2}
                      onChange={(e) => {
                        setComparison([]);
                        setChosen(
                          e.target.checked
                            ? [...chosen, job.id]
                            : chosen.filter((id) => id !== job.id),
                        );
                      }}
                    />{" "}
                    Compare this job
                  </span>
                </label>
              )}
              <div className="card-footer">
                <button
                  className="text-btn"
                  onClick={() =>
                    action(async () => {
                      const item =
                        r ??
                        (await api<Result>(
                          "/saved-jobs/" + job.id + "/evidence",
                        ));
                      open(item);
                    })
                  }
                >
                  View saved match evidence
                </button>
                <button
                  className="secondary"
                  onClick={() =>
                    action(async () => {
                      await remove(job.id);
                      setComparison([]);
                      setChosen(chosen.filter((id) => id !== job.id));
                    })
                  }
                >
                  Remove from saved
                </button>
              </div>
            </article>
          );
        })}
      </div>
    </>
  );
}
