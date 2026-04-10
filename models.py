from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import String, Boolean, Integer, ForeignKey, DateTime, Numeric, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class Plant(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    common_name: Mapped[str] = mapped_column(String(100))
    scientific_name: Mapped[Optional[str]] = mapped_column(String(100))
    #categorization
    category_id: Mapped[Optional[int]] = mapped_column(ForeignKey('category.id'))
    species_id: Mapped[Optional[int]] = mapped_column(ForeignKey('species.id'))
    variety_id: Mapped[Optional[int]] = mapped_column(ForeignKey('variety.id'))

    description: Mapped[Optional[str]] = mapped_column(String(200))
    #key info
    colour: Mapped[Optional[str]] = mapped_column(String(50))
    growth_width: Mapped[Optional[float]] = mapped_column(Float)
    growth_height: Mapped[Optional[float]] = mapped_column(Float)
    fragrant: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    frost_sensitive: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    flowering_period: Mapped[Optional[str]] = mapped_column(String(200))
    light_requirements: Mapped[Optional[str]] = mapped_column(String(200))
    soil_requirements: Mapped[Optional[str]] = mapped_column(String(200))
    #care advice
    planting_advice: Mapped[Optional[str]] = mapped_column(String(200))
    watering_needs: Mapped[Optional[str]] = mapped_column(String(200))
    pruning_needs: Mapped[Optional[str]] = mapped_column(String(200))

    plant_pots: Mapped[list["PlantPot"]] = relationship(back_populates="plant")
    cart_items: Mapped[list["CartItem"]] = relationship(back_populates="plant")


class Pot(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    size: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)

    plant_pots: Mapped[list["PlantPot"]] = relationship(back_populates="pot")


class PlantPot(db.Model):
    plant_id: Mapped[int] = mapped_column(ForeignKey("plant.id"), primary_key=True)
    pot_id: Mapped[int] = mapped_column(ForeignKey("pot.id"), primary_key=True)
    stock_qty: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    image_filename: Mapped[Optional[str]] = mapped_column(String(255))
    price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))

    plant: Mapped["Plant"] = relationship(back_populates="plant_pots")
    pot: Mapped["Pot"] = relationship(back_populates="plant_pots")

class User(db.Model, UserMixin):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_staff: Mapped[bool] = mapped_column(Boolean, default=False)
    carts: Mapped[list["Cart"]] = relationship(back_populates="user")
    orders: Mapped[list["Order"]] = relationship(back_populates="user")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Species(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255))

class Category(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    image_filename: Mapped[Optional[str]] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(String(255))

class Variety(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255))


class Cart(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    user: Mapped["User"] = relationship(back_populates="carts")
    items: Mapped[list["CartItem"]] = relationship(
        back_populates="cart",
        cascade="all, delete-orphan",
        order_by="CartItem.created_at",
    )
    orders: Mapped[list["Order"]] = relationship(back_populates="cart")


class CartItem(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    cart_id: Mapped[int] = mapped_column(ForeignKey("cart.id"), nullable=False, index=True)
    plant_id: Mapped[int] = mapped_column(ForeignKey("plant.id"), nullable=False, index=True)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    unit_price_snapshot: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    plant_name_snapshot: Mapped[str] = mapped_column(String(100), nullable=False)
    image_snapshot: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    cart: Mapped["Cart"] = relationship(back_populates="items")
    plant: Mapped["Plant"] = relationship(back_populates="cart_items")


class Order(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False, index=True)
    cart_id: Mapped[int] = mapped_column(ForeignKey("cart.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), default="pending", nullable=False, index=True)
    subtotal_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    stripe_checkout_session_id: Mapped[Optional[str]] = mapped_column(String(255))
    stripe_payment_intent_id: Mapped[Optional[str]] = mapped_column(String(255))
    payment_status: Mapped[Optional[str]] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    user: Mapped["User"] = relationship(back_populates="orders")
    cart: Mapped["Cart"] = relationship(back_populates="orders")
    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="OrderItem.created_at",
    )


class OrderItem(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("order.id"), nullable=False, index=True)
    plant_id: Mapped[int] = mapped_column(ForeignKey("plant.id"), nullable=False, index=True)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    unit_price_snapshot: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    plant_name_snapshot: Mapped[str] = mapped_column(String(100), nullable=False)
    image_snapshot: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    order: Mapped["Order"] = relationship(back_populates="items")
