from alembic import op

revision = "0003"
down_revision = "0002"


def upgrade():
    op.execute("ALTER TABLE users ADD COLUMN recovery_hash text")
    op.execute("ALTER TABLE saved_jobs ADD COLUMN evidence jsonb")


def downgrade():
    op.execute("ALTER TABLE saved_jobs DROP COLUMN evidence")
    op.execute("ALTER TABLE users DROP COLUMN recovery_hash")
