"""Create Tables

Revision ID: eb9d81cd125b
Revises: cc0eb72a4212
Create Date: 2023-11-21 12:49:08.874283

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eb9d81cd125b'
down_revision: Union[str, None] = 'cc0eb72a4212'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'email')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('email', sa.VARCHAR(), nullable=True))
    # ### end Alembic commands ###
