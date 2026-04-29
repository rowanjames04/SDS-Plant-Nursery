"""add user address table

Revision ID: 7d96b9a1c5f2
Revises: 032b792f13d9
Create Date: 2026-04-24 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "7d96b9a1c5f2"
down_revision = "032b792f13d9"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "user_address",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("line1", sa.String(length=255), nullable=False),
        sa.Column("line2", sa.String(length=255), nullable=True),
        sa.Column("city", sa.String(length=120), nullable=False),
        sa.Column("state", sa.String(length=120), nullable=False),
        sa.Column("postal_code", sa.String(length=20), nullable=False),
        sa.Column("country", sa.String(length=120), nullable=False),
        sa.Column("formatted_address", sa.String(length=500), nullable=False),
        sa.Column("google_place_id", sa.String(length=255), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], name=op.f("fk_user_address_user_id_user")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_address")),
        sa.UniqueConstraint("user_id", name=op.f("uq_user_address_user_id")),
    )
    op.create_index(op.f("ix_user_address_user_id"), "user_address", ["user_id"], unique=True)


def downgrade():
    op.drop_index(op.f("ix_user_address_user_id"), table_name="user_address")
    op.drop_table("user_address")
