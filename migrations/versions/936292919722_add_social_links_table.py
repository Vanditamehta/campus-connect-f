
"""Add social links table

Revision ID: 936292919722
Revises: ed6034e5fa5f
"""

from alembic import op
import sqlalchemy as sa


revision = '936292919722'
down_revision = 'ed6034e5fa5f'
branch_labels = None
depends_on = None


def upgrade():
    inspector = sa.inspect(op.get_bind())

    if not inspector.has_table('social_link'):
        op.create_table(
            'social_link',

            sa.Column(
                'id',
                sa.Integer(),
                primary_key=True
            ),

            sa.Column(
                'user_id',
                sa.Integer(),
                sa.ForeignKey('user.id', ondelete='CASCADE'),
                nullable=False
            ),

            sa.Column(
                'title',
                sa.String(length=50),
                nullable=False
            ),

            sa.Column(
                'url',
                sa.String(length=500),
                nullable=False
            )
        )


def downgrade():
    inspector = sa.inspect(op.get_bind())

    if inspector.has_table('social_link'):
        op.drop_table('social_link')
