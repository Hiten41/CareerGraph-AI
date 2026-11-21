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
            <h2>{selected.job.title}</h2>
            <p>
              {selected.job.company} · {selected.eligibility}
            </p>
            <p>{selected.job.description}</p>
            <h3>Matched requirements</h3>
            <p>
              {selected.explanation.matched.join(", ") ||
                "No verified skill matches"}
            </p>
            <h3>Missing requirements</h3>
            <p>
              {selected.explanation.missing.join(", ") || "None identified"}
            </p>
            <h3>Unknown information</h3>
            <p>
              {selected.unknown.join(", ") || "No unknown active constraints"}
            </p>
            <h3>Rank breakdown</h3>
            <pre>{JSON.stringify(selected.explanation.features, null, 2)}</pre>
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
