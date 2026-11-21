# Audit delivery
Compared with the earlier ranking-snapshot archive, changed or added files are listed below (this report itself is also new).
## Local verification
- Fresh isolated embedded PostgreSQL/pgvector migration and seed, then migration 0002 on the populated database.
- CG_INTEGRATION=1 CG_SEEDED_TESTS=1 python -m pytest -q: 27 passed, including the lexical fallback and provider protocol regressions.
- ruff check apps/api tests scripts; mypy apps/api/app --check-untyped-defs; python -m compileall -q apps/api/app scripts tests.
- npm run lint, npm run typecheck, npm test (one component test), npm run build. BROWSER_CHANNEL=msedge npx playwright test: one scenario passed, including the stale-result regression.
- scripts/evaluate.py, scripts/editorial_eval.py, three runs of scripts/graded_eval.py, scripts/agent_eval.py, scripts/http_benchmark.py and scripts/scale_seed.py executed locally. See the JSON reports under docs.
- No Docker executable, hosted model credentials or cloud deployment. No real user data used in evaluations. Actual GitHub-hosted CI was not executed.
- Remaining gaps include independent human relevance and preference labels, contradictory and adversarial queries in the graded split, broad negation parsing, OCR and unconstrained resume layouts, peak memory under load, and production-scale concurrent ingestion. Hosted model behavior and provider quality remain unmeasured.

## Changed files
- .github/workflows/quality.yml
- README.md
- apps/api/app/agents/orchestrator.py
- apps/api/app/agents/provider.py
- apps/api/app/api/routes.py
- apps/api/app/auth/security.py
- apps/api/app/core/config.py
- apps/api/app/db/session.py
- apps/api/app/ingestion/importer.py
- apps/api/app/ingestion/sources.py
- apps/api/app/main.py
- apps/api/app/retrieval/search.py
- apps/api/app/schemas/domain.py
- apps/api/app/services/resume.py
- apps/api/migrations/versions/0002_provider_consent.py
- apps/web/app/page.tsx
- apps/web/e2e/discovery.spec.ts
- apps/web/features/auth-screen.tsx
- apps/web/features/match-dialog.tsx
- apps/web/types/domain.ts
- compose.yaml
- docs/AGENTS.md
- docs/ARCHITECTURE.md
- docs/AUDIT_DELIVERY.md
- docs/DEMO_SCRIPT.md
- docs/DEPLOYMENT.md
- docs/EVALUATION.md
- docs/REQUIREMENTS_TRACEABILITY.md
- docs/RESUME_BULLETS.md
- docs/RETRIEVAL.md
- docs/SECURITY.md
- docs/agent-results.json
- docs/discovery.png
- docs/editorial-results.json
- docs/graded-results-relaxed-fusion.json
- docs/graded-results-strict-keyword.json
- docs/graded-results.json
- docs/http-load.json
- docs/ingestion-results.json
- infra/api.Dockerfile
- packages/contracts/api.d.ts
- packages/contracts/openapi.json
- scripts/agent_eval.py
- scripts/editorial_eval.py
- scripts/fixtures/editorial.tsv
- scripts/fixtures/graded.txt
- scripts/fixtures/judgments.tsv
- scripts/graded_eval.py
- scripts/hosted_smoke.py
- scripts/http_benchmark.py
- scripts/refresh_source.py
- scripts/scale_seed.py
- tests/test_accounts.py
- tests/test_index_refresh.py
- tests/test_provider.py
- tests/test_resume.py

## Follow-up release
Changed files for this revision include apps/api/app/{agents/orchestrator.py,agents/tools.py,memory/constraints.py,retrieval/eligibility.py,retrieval/search.py,schemas/domain.py}, apps/web/{app/layout.tsx,e2e/discovery.spec.ts}, packages/contracts/{openapi.json,api.d.ts}, scripts/{graded_eval.py,hosted_smoke.py,fixtures/fusion_cases.jsonl}, tests/{test_core.py,test_conversations.py}, docs/{EVALUATION.md,DEPLOYMENT.md,REQUIREMENTS_TRACEABILITY.md,RESUME_BULLETS.md,fusion-results.json}, README.md, .gitignore, infra/api.Dockerfile and .github/workflows/compose-smoke.yml.
Locally, 36 Python tests passed with the database and embedding integrations enabled. The Edge browser scenario passed with contradiction, clear-filters and stale-result coverage. Ruff, mypy, Python compilation, ESLint, TypeScript, Vitest and the Next.js production build passed. The private GitHub repository credits Hiten Arora. Follow the GitHub workflows for remote status. Hosted provider calls require separately configured credentials.
