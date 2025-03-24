"""phone number added

Revision ID: 6835d5b4fb5a
Revises: 
Create Date: 2025-03-24 17:23:36.926848

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6835d5b4fb5a'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users',sa.Column('phone_number',sa.String(),
                                    nullable=True))


def downgrade() -> None:
    pass
