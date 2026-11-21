# Retrieval
Keyword retrieval uses parameterized websearch_to_tsquery and ts_rank_cd. Titles and skills receive A weight and descriptions receive B. The semantic branch encodes query text locally and orders by cosine distance. Each branch retrieves up to 600 IDs. Reciprocal rank fusion sums 1/(60+rank) for each appearance across branches. The final page contains at most 50 jobs.

The engine excludes archived and expired records, retains missing metadata as uncertain and compares salaries only when currency and pay period agree. The reranker averages normalized fusion and positive cosine similarity. Skill overlap, preference match and signed feedback contribute at most 0.020, 0.015 and 0.015 respectively. Unknown requirements remain visible. The score has no calibration to hiring outcomes.
Technical references: [pgvector](https://github.com/pgvector/pgvector) and [Sentence Transformers](https://sbert.net/docs/sentence_transformer/usage/usage.html).

When keyword-only search finds zero strict matches for a plain-language query, it retries with a weighted OR over normalized PostgreSQL lexemes. Quotes, hyphens and explicit OR suppress the fallback. Hybrid and personalized fusion use the strict branch because fusing the relaxed matches lowered graded relevance in the recorded comparison.
