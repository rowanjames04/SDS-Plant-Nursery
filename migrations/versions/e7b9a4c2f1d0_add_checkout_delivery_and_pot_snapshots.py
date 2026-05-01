"""add checkout delivery and pot snapshots

Revision ID: e7b9a4c2f1d0
Revises: bc0e01ca8b24
Create Date: 2026-05-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "e7b9a4c2f1d0"
down_revision = "bc0e01ca8b24"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("cart_item", schema=None) as batch_op:
        batch_op.add_column(sa.Column("pot_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("pot_size_snapshot", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(op.f("fk_cart_item_pot_id_pot"), "pot", ["pot_id"], ["id"])
        batch_op.create_index(op.f("ix_cart_item_pot_id"), ["pot_id"], unique=False)

    with op.batch_alter_table("order", schema=None) as batch_op:
        batch_op.add_column(sa.Column("delivery_fee", sa.Numeric(10, 2), server_default="0", nullable=False))
        batch_op.add_column(sa.Column("delivery_method", sa.String(length=30), nullable=True))
        batch_op.add_column(sa.Column("delivery_distance_km", sa.Numeric(8, 2), nullable=True))
        batch_op.add_column(sa.Column("delivery_line1", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("delivery_line2", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("delivery_city", sa.String(length=120), nullable=True))
        batch_op.add_column(sa.Column("delivery_state", sa.String(length=120), nullable=True))
        batch_op.add_column(sa.Column("delivery_postal_code", sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column("delivery_country", sa.String(length=120), nullable=True))
        batch_op.add_column(sa.Column("delivery_formatted_address", sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column("delivery_google_place_id", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("delivery_latitude", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("delivery_longitude", sa.Float(), nullable=True))

    with op.batch_alter_table("order_item", schema=None) as batch_op:
        batch_op.add_column(sa.Column("pot_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("pot_size_snapshot", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(op.f("fk_order_item_pot_id_pot"), "pot", ["pot_id"], ["id"])
        batch_op.create_index(op.f("ix_order_item_pot_id"), ["pot_id"], unique=False)

    for table in ("cart_item", "order_item"):
        op.execute(sa.text(f"""
            UPDATE {table}
            SET pot_id = (
                SELECT plant_pot.pot_id
                FROM plant_pot
                JOIN pot ON pot.id = plant_pot.pot_id
                WHERE plant_pot.plant_id = {table}.plant_id
                ORDER BY pot.size
                LIMIT 1
            )
            WHERE pot_id IS NULL
        """))
        op.execute(sa.text(f"""
            UPDATE {table}
            SET pot_size_snapshot = (
                SELECT pot.size
                FROM pot
                WHERE pot.id = {table}.pot_id
            )
            WHERE pot_size_snapshot IS NULL
              AND pot_id IS NOT NULL
        """))


def downgrade():
    with op.batch_alter_table("order_item", schema=None) as batch_op:
        batch_op.drop_index(op.f("ix_order_item_pot_id"))
        batch_op.drop_constraint(op.f("fk_order_item_pot_id_pot"), type_="foreignkey")
        batch_op.drop_column("pot_size_snapshot")
        batch_op.drop_column("pot_id")

    with op.batch_alter_table("order", schema=None) as batch_op:
        batch_op.drop_column("delivery_longitude")
        batch_op.drop_column("delivery_latitude")
        batch_op.drop_column("delivery_google_place_id")
        batch_op.drop_column("delivery_formatted_address")
        batch_op.drop_column("delivery_country")
        batch_op.drop_column("delivery_postal_code")
        batch_op.drop_column("delivery_state")
        batch_op.drop_column("delivery_city")
        batch_op.drop_column("delivery_line2")
        batch_op.drop_column("delivery_line1")
        batch_op.drop_column("delivery_distance_km")
        batch_op.drop_column("delivery_method")
        batch_op.drop_column("delivery_fee")

    with op.batch_alter_table("cart_item", schema=None) as batch_op:
        batch_op.drop_index(op.f("ix_cart_item_pot_id"))
        batch_op.drop_constraint(op.f("fk_cart_item_pot_id_pot"), type_="foreignkey")
        batch_op.drop_column("pot_size_snapshot")
        batch_op.drop_column("pot_id")
