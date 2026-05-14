"""Add shop metadata columns to shopify_stores

Revision ID: 005_shop_metadata
Revises: 004_platform_users
Create Date: 2024-01-05 00:00:00
"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op

revision: str = "005_shop_metadata"
down_revision: Union[str, None] = "004_platform_users"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("shopify_stores", sa.Column("shop_name",        sa.Text(), nullable=True))
    op.add_column("shopify_stores", sa.Column("shop_owner_email", sa.Text(), nullable=True))
    op.add_column("shopify_stores", sa.Column("shop_owner_name",  sa.Text(), nullable=True))
    op.add_column("shopify_stores", sa.Column("shop_plan",        sa.Text(), nullable=True))
    op.add_column("shopify_stores", sa.Column("primary_domain",   sa.Text(), nullable=True))


def downgrade() -> None:
    for col in ("shop_name", "shop_owner_email", "shop_owner_name", "shop_plan", "primary_domain"):
        op.drop_column("shopify_stores", col)
