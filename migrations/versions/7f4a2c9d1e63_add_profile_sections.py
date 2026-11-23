
"""Add flexible profile sections

Revision ID: 7f4a2c9d1e63
Revises: 936292919722
"""

from alembic import op
import sqlalchemy as sa


revision = "7f4a2c9d1e63"
down_revision = "936292919722"
branch_labels = None
depends_on = None


def upgrade():
    inspector = sa.inspect(op.get_bind())

    if not inspector.has_table("profile_section"):
        op.create_table(
            "profile_section",

            sa.Column(
                "id",
                sa.Integer(),
                primary_key=True
            ),

            sa.Column(
                "user_id",
                sa.Integer(),
                sa.ForeignKey("user.id", ondelete="CASCADE"),
                nullable=False
            ),

            sa.Column(
                "section_type",
                sa.String(length=50),
                nullable=False
            ),

            sa.Column(
                "data",
                sa.JSON(),
                nullable=False
            ),

            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False
            ),

            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False
            )
        )


def downgrade():
    inspector = sa.inspect(op.get_bind())

    if inspector.has_table("profile_section"):
        op.drop_table("profile_section")
