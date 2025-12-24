"""add chat message sources

Revision ID: 20251202_chat_sources
Revises: 20251202_chat_history
Create Date: 2025-12-02
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20251202_chat_sources"
down_revision = "20251202_chat_history"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("chat_messages", sa.Column("sources", postgresql.JSONB(), nullable=True))


def downgrade():
    op.drop_column("chat_messages", "sources")
