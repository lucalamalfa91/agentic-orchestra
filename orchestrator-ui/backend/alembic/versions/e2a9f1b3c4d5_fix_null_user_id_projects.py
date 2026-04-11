"""fix null user_id in projects created after initial migration

Revision ID: e2a9f1b3c4d5
Revises: d1f4a9c2b8e3
Create Date: 2026-04-11 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e2a9f1b3c4d5'
down_revision: Union[str, Sequence[str], None] = 'd1f4a9c2b8e3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Upgrade schema - set user_id=1 for any projects that still have NULL user_id.

    This catches projects created after the initial migration but before
    the code was updated to set user_id automatically.
    """
    op.execute(
        """
        UPDATE projects
        SET user_id = 1
        WHERE user_id IS NULL
        """
    )


def downgrade() -> None:
    """Downgrade schema - no action needed."""
    pass
