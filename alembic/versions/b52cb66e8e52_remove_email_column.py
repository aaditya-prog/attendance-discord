"""Remove 'Email' column

Revision ID: b52cb66e8e52
Revises: 5b7cfc7f6025
Create Date: 2023-11-21 12:45:10.582551

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b52cb66e8e52"
down_revision: Union[str, None] = "5b7cfc7f6025"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
