"""add order item status

Revision ID: c3f4a8d1e2b9
Revises: a1c4e8d92b7f
"""

from typing import Sequence, Union

from alembic import op


revision: str = "c3f4a8d1e2b9"
down_revision: Union[str, Sequence[str], None] = "a1c4e8d92b7f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE orders DROP CONSTRAINT IF EXISTS ck_orders_status")
    op.execute(
        """ALTER TABLE orders ADD CONSTRAINT ck_orders_status CHECK (
            status IN (
                'pending', 'confirmed', 'preparing', 'ready',
                'served', 'completed', 'cancelled'
            )
        )"""
    )
    op.execute(
        """
        ALTER TABLE order_items
        ADD COLUMN IF NOT EXISTS status VARCHAR(20) NOT NULL DEFAULT 'pending';
        """
    )
    op.execute(
        """
        ALTER TABLE order_items
        ADD CONSTRAINT ck_order_items_status CHECK (
            status IN ('pending', 'preparing', 'ready', 'completed', 'cancelled')
        );
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_orders_status ON orders (status)")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_order_items_status ON order_items (status)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_order_items_status")
    op.execute("DROP INDEX IF EXISTS ix_orders_status")
    op.execute("ALTER TABLE order_items DROP CONSTRAINT IF EXISTS ck_order_items_status")
    op.execute("ALTER TABLE order_items DROP COLUMN IF EXISTS status")
    op.execute("ALTER TABLE orders DROP CONSTRAINT IF EXISTS ck_orders_status")
    op.execute(
        """ALTER TABLE orders ADD CONSTRAINT ck_orders_status CHECK (
            status IN (
                'pending', 'confirmed', 'preparing',
                'ready', 'served', 'cancelled'
            )
        )"""
    )
