"""add_ai_model_column

Revision ID: f3b8c1d2e4a6
Revises: deeeb5b4f909
Create Date: 2026-04-22 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f3b8c1d2e4a6'
down_revision: Union[str, Sequence[str], None] = 'deeeb5b4f909'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('configurations', schema=None) as batch_op:
        batch_op.add_column(sa.Column('ai_model', sa.String(100), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('configurations', schema=None) as batch_op:
        batch_op.drop_column('ai_model')
