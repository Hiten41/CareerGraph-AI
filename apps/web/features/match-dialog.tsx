import { X } from "lucide-react";
import type { Result } from "../types/domain";
import type { RefObject } from "react";
export function MatchDialog({
  dialog,
  selected,
}: {
  dialog: RefObject<HTMLDialogElement | null>;
  selected: Result | null;
}) {
  return (
    <dialog
      aria-labelledby="match-title"
      ref={dialog}
      onClick={(e) => {
        if (e.target === dialog.current) dialog.current.close();
      }}
    >
      <div className="dialog-content">
        <button
          className="close icon-btn"
          aria-label="Close job details"
          onClick={() => dialog.current?.close()}
        >
          <X />
        </button>
        {selected && (
          <>
            <p className="kicker">MATCH EVIDENCE</p>
            <h2 id="match-title">{selected.job.title}</h2>
            <p>
              {selected.job.company} ·{" "}
              {selected.eligibility === "eligible"
                ? "Meets search filters"
                : "Some filters unverified"}
            </p>
            <p>{selected.job.description}</p>
            <h3>Matched requirements</h3>
            <p>
              {selected.explanation.matched.join(", ") ||
                "Your profile has no listed skills in common with this role."}
            </p>
            <h3>Required skills missing from your profile</h3>
            <p>
              {selected.explanation.missing.join(", ") || "None identified"}
            </p>
            <h3>Unknown information</h3>
            <p>
              {selected.unknown.join(", ") ||
                "The listing covers all active search constraints."}
            </p>
            {selected.eligibility === "historical_unknown" ? (
              <p>The original search was not recorded for this bookmark.</p>
            ) : (
              <>
                <h3>Why this role appeared</h3>
                <p>
                  We ranked this role by how closely its title and description
                  fit your search.{" "}
                  {selected.explanation.features.personal_adjustment > 0
                    ? "Your profile, preferences or previous feedback raised its score."
                    : selected.explanation.features.personal_adjustment < 0
                      ? "Your previous feedback lowered its score."
                      : "Personalization did not change its score."}
                </p>
              </>
            )}
            <p className="fine">
              {selected.explanation.score_label}. Last seen:{" "}
              {new Date(selected.job.last_seen_at).toLocaleString()}
            </p>
            {selected.job.synthetic ? (
              <p className="notice">
                Fictional listing — not an application opportunity.
              </p>
            ) : (
              <a
                href={selected.job.url}
                target="_blank"
                rel="noreferrer"
                className="primary"
              >
                View original source
              </a>
            )}
          </>
        )}
      </div>
    </dialog>
  );
}
