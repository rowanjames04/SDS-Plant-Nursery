import os
import unittest
from decimal import Decimal
from types import SimpleNamespace

os.environ["DB_URI"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["SITE_URL"] = "http://testserver"

from app import app, db
from models import (
    Cart,
    CartItem,
    Category,
    Order,
    OrderItem,
    Plant,
    PlantPot,
    Pot,
    Species,
    User,
    UserAddress,
    Variety,
)


class NurseryTestCase(unittest.TestCase):
    def setUp(self):
        app.config.update(
            TESTING=True,
            SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
            SERVER_NAME="localhost.localdomain",
            WTF_CSRF_ENABLED=False,
            STRIPE_SECRET_KEY="sk_test_fake",
            STRIPE_WEBHOOK_SECRET="whsec_test",
            GOOGLE_MAPS_API_KEY="",
            SITE_URL="http://testserver",
        )
        self.app = app
        self.client = app.test_client()
        self.context = app.app_context()
        self.context.push()
        db.session.remove()
        db.drop_all()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()

    def make_user(self, email="customer@example.com", full_name="Customer User", password="password123", is_staff=False):
        user = User(email=email, full_name=full_name, is_staff=is_staff)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user

    def login(self, email="customer@example.com", password="password123"):
        return self.client.post(
            "/login",
            data={"email": email, "password": password},
            follow_redirects=False,
        )

    def make_taxonomy(self):
        category = Category(name="Indoor Plants", description="Plants for inside")
        species = Species(name="Monstera deliciosa", description="Split leaf species")
        variety = Variety(name="Large Form", description="Large foliage")
        db.session.add_all([category, species, variety])
        db.session.commit()
        return category, species, variety

    def make_plant_with_pot(
        self,
        common_name="Swiss Cheese Plant",
        scientific_name="Monstera deliciosa",
        price=Decimal("39.95"),
        stock_qty=10,
        pot_size=230,
        images=None,
    ):
        category, species, variety = self.make_taxonomy()
        plant = Plant(
            common_name=common_name,
            scientific_name=scientific_name,
            category_id=category.id,
            species_id=species.id,
            variety_id=variety.id,
            description="Statement foliage plant",
            images=images if images is not None else ["plants/swiss-cheese-plant.jpg"],
        )
        pot = Pot(size=pot_size)
        db.session.add_all([plant, pot])
        db.session.commit()
        plant_pot = PlantPot(plant_id=plant.id, pot_id=pot.id, price=price, stock_qty=stock_qty)
        db.session.add(plant_pot)
        db.session.commit()
        return plant, pot, plant_pot

    def make_cart_item(self, user, plant, pot, quantity=2, unit_price=Decimal("12.50")):
        cart = Cart(user_id=user.id)
        db.session.add(cart)
        db.session.commit()
        item = CartItem(
            cart_id=cart.id,
            plant_id=plant.id,
            pot_id=pot.id,
            quantity=quantity,
            unit_price_snapshot=unit_price,
            plant_name_snapshot=plant.common_name,
            pot_size_snapshot=pot.size,
            image_snapshot=plant.primary_image,
        )
        db.session.add(item)
        db.session.commit()
        return cart, item

    def make_paid_order(self, user, plant, pot, quantity=1, unit_price=Decimal("20.00")):
        cart = Cart(user_id=user.id, status="ordered")
        db.session.add(cart)
        db.session.commit()
        order = Order(
            user_id=user.id,
            cart_id=cart.id,
            status="preparing",
            subtotal_amount=unit_price * quantity,
            delivery_fee=Decimal("0.00"),
            total_amount=unit_price * quantity,
            payment_status="paid",
        )
        db.session.add(order)
        db.session.commit()
        item = OrderItem(
            order_id=order.id,
            plant_id=plant.id,
            pot_id=pot.id,
            quantity=quantity,
            unit_price_snapshot=unit_price,
            plant_name_snapshot=plant.common_name,
            pot_size_snapshot=pot.size,
            image_snapshot=plant.primary_image,
        )
        db.session.add(item)
        db.session.commit()
        return order, item


def stripe_session(order, payment_status="paid", session_id="cs_test_123"):
    return SimpleNamespace(
        id=session_id,
        payment_status=payment_status,
        payment_intent="pi_test_123",
        metadata={
            "order_id": str(order.id),
            "cart_id": str(order.cart_id),
            "user_id": str(order.user_id),
        },
    )
