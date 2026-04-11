"""add_ai_provider_column

Revision ID: deeeb5b4f909
Revises: e2a9f1b3c4d5
Create Date: 2026-04-11 19:17:05.696850

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'deeeb5b4f909'
down_revision: Union[str, Sequence[str], None] = 'e2a9f1b3c4d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add ai_provider column to configurations table
    with op.batch_alter_table('configurations', schema=None) as batch_op:
        batch_op.add_column(sa.Column('ai_provider', sa.String(50), nullable=False, server_default='openai'))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove ai_provider column from configurations table
    with op.batch_alter_table('configurations', schema=None) as batch_op:
        batch_op.drop_column('ai_provider')
