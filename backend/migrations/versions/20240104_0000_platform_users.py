"""Add platform_users and subscription tables

Revision ID: 004_platform_users
Revises: 003_api_keys
Create Date: 2024-01-04 00:00:00
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "004_platform_users"
down_revision: Union[str, None] = "003_api_keys"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "platform_users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("store_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("shopify_stores.id", ondelete="CASCADE"),
                  nullable=False, unique=True),
        sa.Column("email", sa.Text()),
        sa.Column("name", sa.Text()),

        # Subscription
        sa.Column("subscription_status", sa.Text(), nullable=False,
                  server_default="trial"),         # trial | active | expired | cancelled
        sa.Column("subscription_plan", sa.Text()),  # starter | growth | pro
        sa.Column("trial_ends_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("subscribed_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("subscription_expires_at", sa.TIMESTAMP(timezone=True)),

        # Shopify Billing API
        sa.Column("shopify_charge_id", sa.BigInteger()),
        sa.Column("shopify_charge_status", sa.Text()),  # pending|active|declined|expired

        sa.Column("created_at", sa.TIMESTAMP(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
    )

    op.create_index("idx_platform_users_store", "platform_users", ["store_id"])
    op.create_index("idx_platform_users_email", "platform_users", ["email"])

    # updated_at trigger
    op.execute("""
        CREATE TRIGGER set_updated_at_platform_users
        BEFORE UPDATE ON platform_users
        FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at()
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS set_updated_at_platform_users ON platform_users")
    op.drop_table("platform_users")
