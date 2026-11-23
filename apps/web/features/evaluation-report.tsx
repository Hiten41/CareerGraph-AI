import type { Evaluation } from "../types/domain";
import { EvidenceValue } from "../components/evidence-value";

export function EvaluationReport({ runs }: { runs: Evaluation[] }) {
  const latest = runs[0];
  const comparable = new Map<string, number>();
  for (const run of runs) {
    const { strategy, dataset, queries, ranking_version } = run.metadata;
    const score = run.metrics.ndcg_10;
    if (
      dataset === latest.metadata.dataset &&
      queries === latest.metadata.queries &&
      ranking_version === latest.metadata.ranking_version &&
      typeof strategy === "string" &&
      !comparable.has(strategy) &&
      typeof score === "number"
    )
      comparable.set(strategy, score);
  }
  return (
    <>
      <div className="metric-grid">
        {[
          ["NDCG@10", latest.metrics.ndcg_10],
          ["MRR", latest.metrics.mrr],
          ["p95 latency (ms)", latest.metrics.latency_p95_ms],
          ["Evaluation queries", latest.metadata.queries],
        ].map(
          ([name, value]) =>
            typeof value === "number" && (
              <div className="metric" key={String(name)}>
                <p>{String(name)}</p>
                <strong>
                  {value.toLocaleString(undefined, {
                    maximumFractionDigits: 3,
                  })}
                </strong>
              </div>
            ),
        )}
      </div>
      {comparable.size > 0 && (
        <section className="panel">
          <h2>Ranking quality by strategy</h2>
          <p className="muted">
            NDCG@10 · {String(latest.metadata.dataset)} · latest comparable run
            per strategy
          </p>
          {Array.from(comparable, ([strategy, value]) => (
            <div className="chart-row" key={strategy}>
              <span>{strategy}</span>
              <meter
                aria-label={strategy + " NDCG at ten"}
                title={strategy + ": " + value.toFixed(3)}
                min={0}
                max={1}
                value={value}
              />
              <strong>{value.toFixed(3)}</strong>
            </div>
          ))}
        </section>
      )}
      <h2>Recorded runs</h2>
      {runs.map((run) => (
        <details className="panel" key={run.id}>
          <summary>
            {String(run.metadata.strategy || "Evaluation")} ·{" "}
            {new Date(run.created_at).toLocaleString()}
          </summary>
          <EvidenceValue value={run.metadata} />
          <EvidenceValue value={run.metrics} />
        </details>
      ))}
    </>
  );
}
