"""empty message

Revision ID: 831f4f5783db
Revises: 0ef006b38e32
Create Date: 2018-07-06 14:55:08.376186

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '831f4f5783db'
down_revision = '0ef006b38e32'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('experiment', 'column_extract_code',
               existing_type=sa.VARCHAR(length=600),
               type_=sa.String(length=6000),
               existing_nullable=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('experiment', 'column_extract_code',
               existing_type=sa.String(length=6000),
               type_=sa.VARCHAR(length=600),
               existing_nullable=True)
    # ### end Alembic commands ###