"""Remove 'Email' column 2

Revision ID: cc0eb72a4212
Revises: b52cb66e8e52
Create Date: 2023-11-21 12:46:21.138777

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cc0eb72a4212'
down_revision: Union[str, None] = 'b52cb66e8e52'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
