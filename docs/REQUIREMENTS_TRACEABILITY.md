# Hiring requirement evidence
| Requirement | Module and feature | Verification and demo | Status |
|---|---|---|---|
| LLM prompting, structured outputs, tool calls | agents/orchestrator.py and agents/tools.py, POST chat messages | test_conversations.py covers local dispatch. Show tool evidence. External model routing remains unverified. | Partial |
| Remember context | memory/constraints.py, search_sessions and candidate_preferences | test_conversations.py A–C. Confirm then inspect preferences. | Implemented for documented conversations |
| Match and personalize | retrieval/search.py and ranking/scoring.py, POST jobs/search | test_core.py, scripts/evaluate.py. Compare four stored runs. | Implemented |
| Semantic search over changing inventory | services/embeddings.py and ingestion/importer.py | Default seed embedded 40 records. Second import reported zero changes. Large-index performance unverified. | Partial |
| Evaluate LLM quality | typed evidence and bounded tools | Deterministic agent regressions passed. Hosted tool selection and unsupported-claim rates unmeasured. | Partial |
| Reliable backend and SQL | migrations/versions/0001_initial.py, auth/security.py and API routes | test_accounts.py checks ownership, CSRF, deletion and admin access. | Implemented locally |
| Learn unfamiliar tools from documentation | pgvector cosine operators and Sentence Transformers encode | See RETRIEVAL.md and executed evaluation. | Implemented |
| End-to-end recommendation/search | Next.js profile, discovery, details, saved jobs and FastAPI | e2e/discovery.spec.ts with Edge and real API. | Implemented |
| RAG and LLM evaluations | DB evidence returned to compatible-model tool loop | Local retrieval measured. Hosted RAG response quality unmeasured. | Partial |
| Live side project with real usage | Local synthetic demo | No deployment or user-usage evidence. | Not implemented |
| Docker or cloud deployment | compose.yaml and infra Dockerfiles | Deployment runbook available. Compose startup unverified. | Partial |

## Follow-up verification
- Retrieval and personalization: implemented and exercised on both fixtures. scripts/editorial_eval.py and scripts/fixtures/judgments.tsv define the separate target evaluation. tests/test_core.py covers both preference-driven reversal of near ties and protection of a stronger topical match.
- Changing inventory: scripts/scale_seed.py imported 1,012 additional jobs, with zero changed on retry. tests/test_index_refresh.py verified identity, vector regeneration, keyword freshness and expiry. scripts/http_benchmark.py exercised the authenticated search endpoint with concurrent requests.
- Provider integration: tests/test_provider.py exercised validated tool calls, structured evidence, invalid arguments, untrusted listing text, blocked writes and a labeled timeout fallback. Recent user messages are loaded from owner-checked PostgreSQL sessions. Hosted behavior remains unverified without credentials. scripts/hosted_smoke.py is a live integration probe.
- Deployment: a fresh disk-backed embedded PostgreSQL database passed Alembic migration, seed and search. A clean Docker Compose run is outstanding. Local tests do not verify CI runner or container behavior.

## Audit evidence
| Skill | Exact implementation | Test/result | Demo |
|---|---|---|---|
| Typed tool calling, consent and memory | apps/api/app/agents/provider.py, apps/api/app/agents/orchestrator.py, apps/api/app/api/routes.py, apps/api/migrations/versions/0002_provider_consent.py | tests/test_provider.py; tests/test_accounts.py; docs/agent-results.json records 7/7 tool and 4/4 retention probes | Toggle account consent, confirm a preference, ask for comparison. Live routing unverified. |
| Graded retrieval and personalization | apps/api/app/retrieval/search.py, apps/api/app/ranking/scoring.py, scripts/graded_eval.py | tests/test_core.py; docs/graded-results.json contains 100 queries and four executed strategies | Compare stored graded runs in Evaluation lab. |
| SQL filtering and changing inventory | apps/api/app/ingestion/sources.py, apps/api/app/ingestion/importer.py | tests/test_index_refresh.py includes 603-candidate starvation, pagination, expiry, source validation and duplicate upserts | Run scripts/scale_seed.py twice, then refresh a complete local snapshot. |
| Profile extraction and application integration | apps/api/app/services/resume.py, apps/web/features/match-dialog.tsx | tests/test_resume.py, apps/web/e2e/discovery.spec.ts | Upload a text PDF, confirm extracted details, search and inspect a match. Hosted PDF extraction unverified. |
