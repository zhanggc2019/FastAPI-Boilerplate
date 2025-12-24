"""add chat history tables

Revision ID: 20251202_chat_history
Revises: 20251124_uuid_pk
Create Date: 2025-12-02
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20251202_chat_history"
down_revision = "20251124_uuid_pk"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'chat_conversations'
            ) THEN
                CREATE TABLE chat_conversations (
                    uuid UUID NOT NULL,
                    title VARCHAR(255) NOT NULL,
                    user_uuid UUID NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    PRIMARY KEY (uuid),
                    CONSTRAINT chat_conversations_user_uuid_fkey
                        FOREIGN KEY (user_uuid) REFERENCES users (uuid) ON DELETE CASCADE
                );
            END IF;
        END$$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'chat_messages'
            ) THEN
                CREATE TABLE chat_messages (
                    uuid UUID NOT NULL,
                    role VARCHAR(32) NOT NULL,
                    content TEXT NOT NULL,
                    conversation_uuid UUID NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    PRIMARY KEY (uuid),
                    CONSTRAINT chat_messages_conversation_uuid_fkey
                        FOREIGN KEY (conversation_uuid) REFERENCES chat_conversations (uuid) ON DELETE CASCADE
                );
            END IF;
        END$$;
        """
    )


def downgrade():
    op.drop_table("chat_messages")
    op.drop_table("chat_conversations")
