import { Search, X } from "lucide-react";
export function SearchComposer({
  query,
  setQuery,
  busy,
  submit,
  followup = false,
}: {
  query: string;
  setQuery: (q: string) => void;
  busy: boolean;
  submit: () => void;
  followup?: boolean;
}) {
  return (
    <form
      className="composer"
      onSubmit={(e) => {
        e.preventDefault();
        submit();
      }}
    >
      <Search size={19} aria-hidden="true" />
      <label htmlFor="query" className="sr-only">
        Describe your job search or follow-up
      </label>
      <input
        id="query"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        maxLength={1000}
        placeholder={
          followup
            ? "Refine this search..."
            : "Describe the job you're looking for..."
        }
      />
      {query && (
        <button
          className="clear"
          aria-label="Clear search"
          type="button"
          onClick={() => setQuery("")}
        >
          <X size={16} />
        </button>
      )}
      <button className="search-submit" disabled={busy || !query.trim()}>
        Search
      </button>
    </form>
  );
}
