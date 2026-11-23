import { Bookmark, MapPin, CircleCheck, ThumbsDown } from "lucide-react";
import type { Result } from "../types/domain";
export function JobCard({
  result,
  saved = false,
  onSave,
  onDismiss,
  onOpen,
}: {
  result: Result;
  saved?: boolean;
  onSave: () => void;
  onDismiss: () => void;
  onOpen: () => void;
}) {
  const { job, explanation } = result;
  return (
    <article className="job-card">
      <div className="card-top">
        <span className="company-icon">
          {job.company.slice(0, 2).toUpperCase()}
        </span>
        <div>
          <p className="eyebrow">{job.company}</p>
          <button className="job-title" onClick={onOpen}>
            {job.title}
          </button>
        </div>
        <button
          className="icon-btn"
          aria-pressed={saved}
          disabled={saved}
          aria-label={`${saved ? "Saved" : "Save"} ${job.title}`}
          onClick={onSave}
        >
          <Bookmark size={19} fill={saved ? "currentColor" : "none"} />
        </button>
      </div>
      <div className="job-meta">
        <span>
          <MapPin size={14} />
          {job.location || "Location unknown"}
        </span>
        <span>{job.mode || "Mode unknown"}</span>
        <span>{job.employment || "Type unknown"}</span>
      </div>
      <p className="salary">
        {job.salary !== null
          ? `${job.currency || "?"} ${Number(job.salary).toLocaleString()} / ${job.period || "unknown period"}`
          : "Compensation not disclosed"}
      </p>
      <div className="match">
        <CircleCheck size={16} />
        <strong>
          {result.eligibility === "eligible"
            ? "Meets search filters"
            : "Some filters unverified"}
        </strong>
        <span>· {explanation.matched.length} matching skills</span>
      </div>
      <div className="tags">
        {explanation.matched.map((s) => (
          <span key={s}>{s}</span>
        ))}
      </div>
      {explanation.missing.length > 0 && (
        <p className="muted">
          Skills to build: {explanation.missing.join(", ")}
        </p>
      )}
      {result.unknown.length > 0 && (
        <p className="muted">Unverified: {result.unknown.join(", ")}</p>
      )}
      <div className="card-footer">
        <span>
          {job.synthetic ? "Fictional demo listing" : "Source listing"}
        </span>
        <button className="text-btn" onClick={onOpen}>
          View match evidence
        </button>
        <button
          className="icon-btn"
          aria-label={`Dismiss ${job.title}`}
          onClick={onDismiss}
        >
          <ThumbsDown size={16} />
        </button>
      </div>
    </article>
  );
}
