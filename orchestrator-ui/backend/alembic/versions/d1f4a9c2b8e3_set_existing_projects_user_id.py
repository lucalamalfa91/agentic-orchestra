"""set existing projects user_id to 1

Revision ID: d1f4a9c2b8e3
Revises: c9a3e8f1d45a
Create Date: 2026-04-11 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd1f4a9c2b8e3'
down_revision: Union[str, Sequence[str], None] = 'c9a3e8f1d45a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - set user_id=1 for existing projects with NULL user_id."""
    # Update all existing projects with NULL user_id to user_id=1
    # This assumes user_id=1 exists (created during initial auth)
    op.execute(
        """
        UPDATE projects
        SET user_id = 1
        WHERE user_id IS NULL
        """
    )


def downgrade() -> None:
    """Downgrade schema - set user_id back to NULL."""
    # Revert changes (set back to NULL)
    op.execute(
        """
        UPDATE projects
        SET user_id = NULL
        WHERE user_id = 1
        """
    )
