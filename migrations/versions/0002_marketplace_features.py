"""Additional marketplace tables."""
revision='0002_marketplace_features'
down_revision='0001_initial'
branch_labels=None
depends_on=None

def upgrade():
    # Tables are also created by create_app() for fresh installs.
    # This migration is intentionally a no-op marker for compatibility with the
    # project's lightweight initial migration strategy.
    pass

def downgrade():
    pass
