# Storage and query plans
Users own hashed sessions, one profile document, preference rows, conversation sessions, feedback and bookmarks. Cascading foreign keys delete their private records. Messages and tool calls belong to a conversation. Profiles and historical payloads use JSONB. Job constraints use typed columns so SQL can filter before limiting candidates.

A unique source and external ID pair controls upserts. GIN indexes the generated weighted search vector. HNSW uses cosine distance over 384-dimensional embeddings. A composite index covers status and common eligibility predicates. Owner and chronological indexes serve account and conversation lookups. Unique user/job pairs prevent duplicate saves and feedback.
Run scripts/query_plan.py against the seed to refresh [the actual planner output](query-plan.txt). A small fixture cannot establish the benefit of the ANN index at production scale.
