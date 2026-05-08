import unittest
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from tests.helpers import NurseryTestCase, stripe_session
from app import (
    address_dict_from_user_address,
    build_order_summary,
    db,
    expire_stripe_checkout_session,
    fulfill_stripe_checkout_session,
    mark_stripe_checkout_session_failed,
    sync_payment_pending_order,
)
from models import Order, PlantPot, UserAddress
from payments.checkout import amount_to_cents, create_checkout_session


class Sprint4CheckoutFulfillmentTests(NurseryTestCase):
    def test_amount_to_cents_rounds_currency_values(self):
        self.assertEqual(amount_to_cents(Decimal("12.345")), 1235)

    def test_address_dict_preserves_verified_address_fields(self):
        user = self.make_user()
        address = UserAddress(
            user_id=user.id,
            line1="1 Nursery Road",
            line2="Unit 2",
            city="Jilliby",
            state="NSW",
            postal_code="2259",
            country="Australia",
            formatted_address="1 Nursery Road, Jilliby NSW 2259, Australia",
            google_place_id="place_123",
            latitude=-33.2610013,
            longitude=151.3974672,
        )

        result = address_dict_from_user_address(address)

        self.assertEqual(result["line2"], "Unit 2")
        self.assertEqual(result["google_place_id"], "place_123")

    def test_sync_payment_pending_order_sets_delivery_and_total(self):
        user = self.make_user()
        plant, pot, _ = self.make_plant_with_pot()
        cart, _ = self.make_cart_item(user, plant, pot, quantity=2, unit_price=Decimal("20.00"))
        address = {
            "line1": "1 Nursery Road",
            "line2": "",
            "city": "Jilliby",
            "state": "NSW",
            "postal_code": "2259",
            "country": "Australia",
            "formatted_address": "1 Nursery Road, Jilliby NSW 2259, Australia",
            "google_place_id": "place_123",
            "latitude": -33.2610013,
            "longitude": 151.3974672,
        }

        order = sync_payment_pending_order(
            user,
            cart,
            "delivery",
            address=address,
            delivery_fee=Decimal("60.00"),
            delivery_distance=Decimal("0.00"),
        )
        summary = build_order_summary(order)

        self.assertEqual(order.status, "payment_pending")
        self.assertEqual(order.delivery_method, "delivery")
        self.assertEqual(summary["total"], Decimal("100.00"))

    def test_fulfill_stripe_checkout_session_deducts_stock_and_marks_order_paid(self):
        user = self.make_user()
        plant, pot, plant_pot = self.make_plant_with_pot(stock_qty=5)
        order, _ = self.make_paid_order(user, plant, pot, quantity=2)
        order.payment_status = "unpaid"
        order.status = "payment_pending"
        order.cart.status = "active"

        fulfilled = fulfill_stripe_checkout_session("cs_test_123", stripe_session(order))

        self.assertEqual(fulfilled.payment_status, "paid")
        self.assertEqual(fulfilled.status, "preparing")
        self.assertEqual(fulfilled.cart.status, "ordered")
        self.assertEqual(db.session.get(PlantPot, (plant.id, pot.id)).stock_qty, 3)

    def test_fulfill_stripe_checkout_session_is_idempotent_after_payment(self):
        user = self.make_user()
        plant, pot, _ = self.make_plant_with_pot(stock_qty=5)
        order, _ = self.make_paid_order(user, plant, pot, quantity=2)

        fulfilled = fulfill_stripe_checkout_session("cs_test_123", stripe_session(order))

        self.assertEqual(fulfilled.id, order.id)
        self.assertEqual(db.session.get(PlantPot, (plant.id, pot.id)).stock_qty, 5)

    def test_fulfill_stripe_checkout_session_fails_when_stock_is_short(self):
        user = self.make_user()
        plant, pot, _ = self.make_plant_with_pot(stock_qty=1)
        order, _ = self.make_paid_order(user, plant, pot, quantity=2)
        order.payment_status = "unpaid"

        with self.assertRaises(ValueError):
            fulfill_stripe_checkout_session("cs_test_123", stripe_session(order))

        self.assertEqual(db.session.get(Order, order.id).payment_status, "failed")

    def test_failed_stripe_session_restores_cart_to_active(self):
        user = self.make_user()
        plant, pot, _ = self.make_plant_with_pot()
        order, _ = self.make_paid_order(user, plant, pot)
        order.payment_status = "unpaid"
        order.cart.status = "checked_out"

        mark_stripe_checkout_session_failed(stripe_session(order, payment_status="failed"))

        self.assertEqual(db.session.get(Order, order.id).payment_status, "failed")
        self.assertEqual(db.session.get(Order, order.id).cart.status, "active")

    def test_expired_stripe_session_restores_cart_to_active(self):
        user = self.make_user()
        plant, pot, _ = self.make_plant_with_pot()
        order, _ = self.make_paid_order(user, plant, pot)
        order.payment_status = "unpaid"
        order.cart.status = "checked_out"

        expire_stripe_checkout_session(stripe_session(order, payment_status="expired"))

        self.assertEqual(db.session.get(Order, order.id).payment_status, "expired")
        self.assertEqual(db.session.get(Order, order.id).cart.status, "active")

    def test_create_checkout_session_includes_products_delivery_and_metadata(self):
        user = self.make_user()
        plant, pot, _ = self.make_plant_with_pot()
        order, _ = self.make_paid_order(user, plant, pot, quantity=2, unit_price=Decimal("12.00"))
        order.delivery_fee = Decimal("60.00")
        order.total_amount = Decimal("84.00")
        fake_session = SimpleNamespace(id="cs_created", url="https://stripe.test/checkout")

        with patch("payments.checkout.stripe.checkout.Session.create", return_value=fake_session) as create:
            result = create_checkout_session(order)

        payload = create.call_args.kwargs
        self.assertEqual(result.id, "cs_created")
        self.assertEqual(payload["line_items"][0]["quantity"], 2)
        self.assertEqual(payload["line_items"][1]["price_data"]["product_data"]["name"], "Local delivery")
        self.assertEqual(payload["metadata"]["order_id"], str(order.id))


if __name__ == "__main__":
    unittest.main()
