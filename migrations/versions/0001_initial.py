"""CareerHub initial migration marker.

CareerHub creates its initial SQLite schema automatically on first application startup.
Flask-Migrate/Alembic is retained so later phases can use tracked schema migrations.
"""
revision='0001_initial'
down_revision=None
branch_labels=None
depends_on=None

def upgrade():
    pass

def downgrade():
    pass
