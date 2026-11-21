from alembic import op

revision = "0001"
down_revision = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("""
    CREATE TABLE users (id uuid PRIMARY KEY, email text NOT NULL UNIQUE, password_hash text NOT NULL,
      role text NOT NULL DEFAULT 'candidate' CHECK(role IN ('candidate','admin')), created_at timestamptz NOT NULL DEFAULT now());
    CREATE TABLE auth_sessions (token_hash text PRIMARY KEY, user_id uuid NOT NULL REFERENCES users ON DELETE CASCADE,
      csrf text NOT NULL, expires_at timestamptz NOT NULL);
    CREATE INDEX auth_sessions_user ON auth_sessions(user_id);
    CREATE TABLE candidate_profiles (user_id uuid PRIMARY KEY REFERENCES users ON DELETE CASCADE,
      data jsonb NOT NULL DEFAULT '{}', updated_at timestamptz NOT NULL DEFAULT now());
    CREATE TABLE candidate_preferences (user_id uuid REFERENCES users ON DELETE CASCADE, preference text NOT NULL,
      created_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(user_id, preference));
    CREATE TABLE jobs (id uuid PRIMARY KEY, source text NOT NULL, external_id text NOT NULL, title text NOT NULL,
      company text NOT NULL, description text NOT NULL, skills jsonb NOT NULL, optional_skills jsonb NOT NULL,
      employment text, mode text, location text, graduation_year integer, salary numeric CHECK(salary>=0), currency text,
      period text, experience numeric CHECK(experience>=0), domain text,
      status text NOT NULL CHECK(status IN ('active','expired','unknown','archived')), url text NOT NULL,
      synthetic boolean NOT NULL, content_hash text NOT NULL, embedding vector(384),
      search_vector tsvector GENERATED ALWAYS AS (
        setweight(to_tsvector('english', title), 'A') ||
        setweight(to_tsvector('english', skills::text), 'A') ||
        setweight(to_tsvector('english', description), 'B')) STORED,
      created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
      last_seen_at timestamptz NOT NULL DEFAULT now(), UNIQUE(source, external_id));
    CREATE INDEX jobs_fts ON jobs USING gin(search_vector);
    CREATE INDEX jobs_vector ON jobs USING hnsw(embedding vector_cosine_ops);
    CREATE INDEX jobs_filters ON jobs(status, employment, mode, graduation_year);
    CREATE TABLE search_sessions (id uuid PRIMARY KEY, user_id uuid NOT NULL REFERENCES users ON DELETE CASCADE,
      query text NOT NULL DEFAULT '', constraints jsonb NOT NULL DEFAULT '{}', last_jobs jsonb NOT NULL DEFAULT '[]',
      pending_preference text, created_at timestamptz NOT NULL DEFAULT now());
    CREATE INDEX search_sessions_owner ON search_sessions(user_id);
    CREATE TABLE search_messages (id uuid PRIMARY KEY, session_id uuid NOT NULL REFERENCES search_sessions ON DELETE CASCADE,
      role text NOT NULL, content jsonb NOT NULL, created_at timestamptz NOT NULL DEFAULT now());
    CREATE INDEX messages_session ON search_messages(session_id, created_at);
    CREATE TABLE saved_jobs (user_id uuid REFERENCES users ON DELETE CASCADE, job_id uuid REFERENCES jobs ON DELETE CASCADE,
      created_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(user_id, job_id));
    CREATE TABLE job_feedback (user_id uuid REFERENCES users ON DELETE CASCADE, job_id uuid REFERENCES jobs ON DELETE CASCADE,
      value integer NOT NULL CHECK(value IN (-1,1)), PRIMARY KEY(user_id,job_id));
    CREATE TABLE agent_tool_calls (id uuid PRIMARY KEY, session_id uuid REFERENCES search_sessions ON DELETE CASCADE,
      tool text NOT NULL, success boolean NOT NULL, created_at timestamptz NOT NULL DEFAULT now());
    CREATE TABLE ingestion_runs (id uuid PRIMARY KEY, count integer NOT NULL, created_at timestamptz NOT NULL DEFAULT now());
    CREATE TABLE evaluation_runs (id uuid PRIMARY KEY, metadata jsonb NOT NULL, metrics jsonb NOT NULL,
      created_at timestamptz NOT NULL DEFAULT now());
    """)


def downgrade():
    for table in (
        "evaluation_runs",
        "ingestion_runs",
        "agent_tool_calls",
        "job_feedback",
        "saved_jobs",
        "search_messages",
        "search_sessions",
        "jobs",
        "candidate_preferences",
        "candidate_profiles",
        "auth_sessions",
        "users",
    ):
        op.execute(f"DROP TABLE {table}")
