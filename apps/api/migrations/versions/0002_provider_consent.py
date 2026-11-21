from alembic import op

revision = "0002"
down_revision = "0001"


def upgrade():
    op.execute("ALTER TABLE users ADD COLUMN provider_consent boolean NOT NULL DEFAULT false")


def downgrade():
    op.execute("ALTER TABLE users DROP COLUMN provider_consent")
