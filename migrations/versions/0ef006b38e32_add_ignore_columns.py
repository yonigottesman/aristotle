"""add ignore columns

Revision ID: 0ef006b38e32
Revises: 7f9f5faedb3d
Create Date: 2018-05-17 12:27:57.700521

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0ef006b38e32'
down_revision = '7f9f5faedb3d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('experiment', sa.Column('column_ignore_list', sa.String(length=2000), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('experiment', 'column_ignore_list')
    # ### end Alembic commands ###