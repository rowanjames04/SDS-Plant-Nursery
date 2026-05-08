import unittest
from decimal import Decimal

from tests.helpers import NurseryTestCase
from app import (
    build_order_summary,
    db,
    delivery_quote_for_address,
    distance_km,
    sync_order_with_cart,
    validate_cart_stock,
)
from models import CartItem, PlantPot


class Sprint2InventoryScopeTests(NurseryTestCase):
    def test_plant_pot_tracks_stock_and_price_for_specific_combination(self):
        plant, pot, plant_pot = self.make_plant_with_pot(price=Decimal("18.50"), stock_qty=7)

        saved = db.session.get(PlantPot, (plant.id, pot.id))

        self.assertEqual(saved.stock_qty, 7)
        self.assertEqual(saved.price, Decimal("18.50"))

    def test_primary_image_uses_first_image_from_multiple_image_pool(self):
        plant, _, _ = self.make_plant_with_pot(images=["plants/one.jpg", "plants/two.jpg"])

        self.assertEqual(plant.primary_image, "plants/one.jpg")

    def test_primary_image_is_none_when_no_images_exist(self):
        plant, _, _ = self.make_plant_with_pot(images=[])

        self.assertIsNone(plant.primary_image)

    def test_validate_cart_stock_reports_shortage(self):
        user = self.make_user()
        plant, pot, _ = self.make_plant_with_pot(stock_qty=1)
        cart, _ = self.make_cart_item(user, plant, pot, quantity=2)

        errors = validate_cart_stock(cart)

        self.assertEqual(len(errors), 1)
        self.assertIn("Only 1 Swiss Cheese Plant", errors[0])

    def test_sync_order_with_cart_copies_snapshot_values(self):
        user = self.make_user()
        plant, pot, _ = self.make_plant_with_pot()
        cart, item = self.make_cart_item(user, plant, pot, quantity=2, unit_price=Decimal("15.25"))

        order = sync_order_with_cart(user, cart)
        summary = build_order_summary(order)

        self.assertEqual(order.items[0].plant_name_snapshot, item.plant_name_snapshot)
        self.assertEqual(summary["subtotal"], Decimal("30.50"))
        self.assertEqual(summary["item_count"], 2)

    def test_delivery_quote_applies_local_fee_under_free_delivery_count(self):
        address = {"latitude": -33.2610013, "longitude": 151.3974672}

        distance, fee, error = delivery_quote_for_address(address, plant_count=2)

        self.assertEqual(distance, Decimal("0.00"))
        self.assertEqual(fee, Decimal("60.00"))
        self.assertIsNone(error)

    def test_delivery_quote_is_free_for_bulk_orders(self):
        address = {"latitude": -33.2610013, "longitude": 151.3974672}

        _, fee, error = delivery_quote_for_address(address, plant_count=10)

        self.assertEqual(fee, Decimal("0.00"))
        self.assertIsNone(error)

    def test_delivery_quote_rejects_addresses_outside_radius(self):
        address = {"latitude": -33.8688, "longitude": 151.2093}

        distance, fee, error = delivery_quote_for_address(address, plant_count=1)

        self.assertGreater(distance, Decimal("20.00"))
        self.assertIsNone(fee)
        self.assertIn("outside our 20km delivery radius", error)

    def test_distance_returns_none_for_incomplete_coordinates(self):
        self.assertIsNone(distance_km(None, 151.3974672))


if __name__ == "__main__":
    unittest.main()
