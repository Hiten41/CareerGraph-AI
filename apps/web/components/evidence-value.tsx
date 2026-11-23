export function EvidenceValue({ value }: { value: unknown }) {
  if (value == null) return <span>Unavailable</span>;
  if (Array.isArray(value)) {
    return value.length ? (
      <ul className="evidence-list">
        {value.map((item, i) => (
          <li key={i}>
            <EvidenceValue value={item} />
          </li>
        ))}
      </ul>
    ) : (
      <span>None recorded</span>
    );
  }
  if (typeof value === "object") {
    const entries = Object.entries(value);
    return entries.length ? (
      <dl className="evidence-fields">
        {entries.map(([label, item]) => (
          <div key={label}>
            <dt>{label.replaceAll("_", " ")}</dt>
            <dd>
              <EvidenceValue value={item} />
            </dd>
          </div>
        ))}
      </dl>
    ) : (
      <span>None recorded</span>
    );
  }
  if (typeof value === "boolean") return <span>{value ? "Yes" : "No"}</span>;
  return (
    <span>
      {typeof value === "number"
        ? value.toLocaleString(undefined, { maximumFractionDigits: 3 })
        : String(value)}
    </span>
  );
}
