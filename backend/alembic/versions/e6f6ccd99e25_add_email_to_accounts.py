"""add_email_to_accounts

Revision ID: e6f6ccd99e25
Revises: 977deef87685
Create Date: 2026-03-18 03:22:28.568217

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e6f6ccd99e25'
down_revision: Union[str, Sequence[str], None] = '977deef87685'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('accounts', sa.Column('email', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('accounts', 'email')
