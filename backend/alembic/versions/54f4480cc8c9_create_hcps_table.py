"""create hcps table

Revision ID: 54f4480cc8c9
Revises: 913242044bef
Create Date: 2026-09-12 23:29:54.100006

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '54f4480cc8c9'
down_revision: Union[str, Sequence[str], None] = '913242044bef'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'hcps',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('specialty', sa.String(length=150), nullable=False),
        sa.Column('email', sa.String(length=50), nullable=True),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('organization', sa.String(length=100), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False
        ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index(
        'ix_hcps_email',
        'hcps',
        ['email'],
        unique=False
    )

    op.create_index(
        'ix_hcps_name',
        'hcps',
        ['name'],
        unique=False
    )

    op.create_index(
        'ix_hcps_specialty',
        'hcps',
        ['specialty'],
        unique=False
    )

def downgrade() -> None:
    op.drop_index('ix_hcps_specialty', table_name='hcps')
    op.drop_index('ix_hcps_name', table_name='hcps')
    op.drop_index('ix_hcps_email', table_name='hcps')
    op.drop_table('hcps')