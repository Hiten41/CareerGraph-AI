from app.db.session import engine
from sqlalchemy import text
from pathlib import Path

with engine.connect() as db:
    Path("docs/query-plan.txt").write_text(
        "\n".join(
            db.execute(
                text(
                    "EXPLAIN (ANALYZE,BUFFERS) SELECT id FROM jobs WHERE search_vector @@ plainto_tsquery('english','Python')"
                )
            ).scalars()
        )
    )
