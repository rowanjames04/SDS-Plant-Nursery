"""add cart and order tables

Revision ID: bf7470231526
Revises: 4af8115c82bd
Create Date: 2026-04-10 17:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "bf7470231526"
down_revision = "4af8115c82bd"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("plant", schema=None) as batch_op:
        batch_op.alter_column(
            "price",
            existing_type=sa.Float(),
            type_=sa.Numeric(10, 2),
            existing_nullable=True,
        )

    op.create_table(
        "cart",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], name=op.f("fk_cart_user_id_user")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cart")),
    )
    op.create_index(op.f("ix_cart_status"), "cart", ["status"], unique=False)
    op.create_index(op.f("ix_cart_user_id"), "cart", ["user_id"], unique=False)

    op.create_table(
        "order",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("cart_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("subtotal_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("total_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("stripe_checkout_session_id", sa.String(length=255), nullable=True),
        sa.Column("stripe_payment_intent_id", sa.String(length=255), nullable=True),
        sa.Column("payment_status", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["cart_id"], ["cart.id"], name=op.f("fk_order_cart_id_cart")),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], name=op.f("fk_order_user_id_user")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_order")),
    )
    op.create_index(op.f("ix_order_cart_id"), "order", ["cart_id"], unique=False)
    op.create_index(op.f("ix_order_status"), "order", ["status"], unique=False)
    op.create_index(op.f("ix_order_user_id"), "order", ["user_id"], unique=False)

    op.create_table(
        "cart_item",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cart_id", sa.Integer(), nullable=False),
        sa.Column("plant_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price_snapshot", sa.Numeric(10, 2), nullable=False),
        sa.Column("plant_name_snapshot", sa.String(length=100), nullable=False),
        sa.Column("image_snapshot", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["cart_id"], ["cart.id"], name=op.f("fk_cart_item_cart_id_cart")),
        sa.ForeignKeyConstraint(["plant_id"], ["plant.id"], name=op.f("fk_cart_item_plant_id_plant")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cart_item")),
    )
    op.create_index(op.f("ix_cart_item_cart_id"), "cart_item", ["cart_id"], unique=False)
    op.create_index(op.f("ix_cart_item_plant_id"), "cart_item", ["plant_id"], unique=False)

    op.create_table(
        "order_item",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("plant_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price_snapshot", sa.Numeric(10, 2), nullable=False),
        sa.Column("plant_name_snapshot", sa.String(length=100), nullable=False),
        sa.Column("image_snapshot", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["order.id"], name=op.f("fk_order_item_order_id_order")),
        sa.ForeignKeyConstraint(["plant_id"], ["plant.id"], name=op.f("fk_order_item_plant_id_plant")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_order_item")),
    )
    op.create_index(op.f("ix_order_item_order_id"), "order_item", ["order_id"], unique=False)
    op.create_index(op.f("ix_order_item_plant_id"), "order_item", ["plant_id"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_order_item_plant_id"), table_name="order_item")
    op.drop_index(op.f("ix_order_item_order_id"), table_name="order_item")
    op.drop_table("order_item")

    op.drop_index(op.f("ix_cart_item_plant_id"), table_name="cart_item")
    op.drop_index(op.f("ix_cart_item_cart_id"), table_name="cart_item")
    op.drop_table("cart_item")

    op.drop_index(op.f("ix_order_user_id"), table_name="order")
    op.drop_index(op.f("ix_order_status"), table_name="order")
    op.drop_index(op.f("ix_order_cart_id"), table_name="order")
    op.drop_table("order")

    op.drop_index(op.f("ix_cart_user_id"), table_name="cart")
    op.drop_index(op.f("ix_cart_status"), table_name="cart")
    op.drop_table("cart")

    with op.batch_alter_table("plant", schema=None) as batch_op:
        batch_op.alter_column(
            "price",
            existing_type=sa.Numeric(10, 2),
            type_=sa.Float(),
            existing_nullable=True,
        )
