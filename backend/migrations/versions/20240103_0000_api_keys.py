"""Add api_keys table

Revision ID: 003_api_keys
Revises: 002_kpi_views
Create Date: 2024-01-03 00:00:00
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003_api_keys"
down_revision: Union[str, None] = "002_kpi_views"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "api_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("store_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("shopify_stores.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),            # human-readable label
        sa.Column("key_hash", sa.Text(), nullable=False, unique=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("last_used_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("idx_api_keys_hash", "api_keys", ["key_hash"])
    op.create_index("idx_api_keys_store", "api_keys", ["store_id"])


def downgrade() -> None:
    op.drop_table("api_keys")
