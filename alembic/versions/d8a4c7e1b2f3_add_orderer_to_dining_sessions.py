"""add orderer ownership to dining sessions

Revision ID: d8a4c7e1b2f3
Revises: c3f4a8d1e2b9
"""

from typing import Sequence, Union

from alembic import op


revision: str = "d8a4c7e1b2f3"
down_revision: Union[str, Sequence[str], None] = "c3f4a8d1e2b9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE dining_sessions ADD COLUMN IF NOT EXISTS "
        "orderer_token_hash VARCHAR(64)"
    )
    op.execute(
        "ALTER TABLE dining_sessions ADD COLUMN IF NOT EXISTS "
        "orderer_claimed_at TIMESTAMP WITH TIME ZONE"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE dining_sessions DROP COLUMN IF EXISTS orderer_claimed_at")
    op.execute("ALTER TABLE dining_sessions DROP COLUMN IF EXISTS orderer_token_hash")