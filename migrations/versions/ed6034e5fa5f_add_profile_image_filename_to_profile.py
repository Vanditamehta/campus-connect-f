
"""Add profile image filename to profile

Revision ID: ed6034e5fa5f
Revises: cb33784e23f3
Create Date: 2026-11-23 16:59:35.665015

"""
from alembic import op
import sqlalchemy as sa


revision = 'ed6034e5fa5f'
down_revision = 'cb33784e23f3'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'profile',
        sa.Column(
            'profile_image_filename',
            sa.String(length=255),
            nullable=True
        )
    )


def downgrade():
    op.drop_column('profile', 'profile_image_filename')
