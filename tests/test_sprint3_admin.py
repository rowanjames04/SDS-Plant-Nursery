import io
import unittest
from unittest.mock import patch

from tests.helpers import NurseryTestCase
from app import db
from models import Category, Order, Plant, PlantPot, Pot


class Sprint3AdminTests(NurseryTestCase):
    def setUp(self):
        super().setUp()
        self.staff = self.make_user(email="staff@example.com", full_name="Staff User", is_staff=True)
        self.customer = self.make_user(email="customer@example.com", full_name="Customer User", is_staff=False)

    def test_admin_routes_require_staff_user(self):
        self.login(email="customer@example.com")

        response = self.client.get("/admin/home")

        self.assertEqual(response.status_code, 403)

    def test_staff_can_create_pot_size(self):
        self.login(email="staff@example.com")

        response = self.client.post("/admin/pots/new", data={"size": "180"}, follow_redirects=False)

        self.assertEqual(response.status_code, 302)
        self.assertIsNotNone(Pot.query.filter_by(size=180).first())

    def test_duplicate_pot_size_is_not_created(self):
        self.login(email="staff@example.com")
        db_pot = Pot(size=180)
        db.session.add(db_pot)
        db.session.commit()

        self.client.post("/admin/pots/new", data={"size": "180"})

        self.assertEqual(Pot.query.filter_by(size=180).count(), 1)

    def test_staff_can_create_update_and_delete_category(self):
        self.login(email="staff@example.com")

        self.client.post("/admin/categories/new", data={"name": "Ferns", "description": "Shade plants"})
        category = Category.query.filter_by(name="Ferns").first()
        self.client.post(
            f"/admin/categories/{category.id}/update",
            data={"name": "Indoor Ferns", "description": "Filtered light"},
        )
        self.client.post(f"/admin/categories/{category.id}/delete")

        self.assertIsNone(Category.query.filter_by(name="Indoor Ferns").first())

    def test_taxonomy_in_use_cannot_be_deleted(self):
        self.login(email="staff@example.com")
        plant, _, _ = self.make_plant_with_pot()

        self.client.post(f"/admin/categories/{plant.category_id}/delete")

        self.assertIsNotNone(db.session.get(Category, plant.category_id))

    def test_staff_can_assign_and_update_pot_inventory_for_plant(self):
        self.login(email="staff@example.com")
        plant, _, _ = self.make_plant_with_pot()
        pot = Pot(size=300)
        db.session.add(pot)
        db.session.commit()

        self.client.post(
            f"/admin/plants/{plant.id}/assign-pot",
            data={"pot_id": str(pot.id), "price": "74.00", "stock_qty": "4"},
        )
        self.client.post(
            f"/admin/plants/{plant.id}/pots/{pot.id}/update",
            data={"price": "79.00", "stock_qty": "3"},
        )

        plant_pot = db.session.get(PlantPot, (plant.id, pot.id))
        self.assertEqual(plant_pot.stock_qty, 3)
        self.assertEqual(str(plant_pot.price), "79.00")

    def test_staff_can_upload_and_reorder_multiple_images(self):
        self.login(email="staff@example.com")
        plant, _, _ = self.make_plant_with_pot(images=[])

        with patch("admin._save_plant_image", side_effect=["plants/a.jpg", "plants/b.jpg"]):
            self.client.post(
                f"/admin/plants/{plant.id}/images/upload",
                data={
                    "images": [
                        (io.BytesIO(b"image-a"), "a.jpg"),
                        (io.BytesIO(b"image-b"), "b.jpg"),
                    ],
                },
                content_type="multipart/form-data",
            )
        self.client.post(
            f"/admin/plants/{plant.id}/images/reorder",
            data={"images[]": ["plants/b.jpg", "plants/a.jpg"]},
        )

        self.assertEqual(db.session.get(Plant, plant.id).images, ["plants/b.jpg", "plants/a.jpg"])

    def test_staff_can_update_order_status_to_valid_fulfilment_state(self):
        self.login(email="staff@example.com")
        plant, pot, _ = self.make_plant_with_pot()
        order, _ = self.make_paid_order(self.customer, plant, pot)

        self.client.post(f"/admin/orders/{order.id}/status", data={"status": "dispatched"})

        self.assertEqual(db.session.get(Order, order.id).status, "dispatched")

    def test_invalid_order_status_is_ignored(self):
        self.login(email="staff@example.com")
        plant, pot, _ = self.make_plant_with_pot()
        order, _ = self.make_paid_order(self.customer, plant, pot)

        self.client.post(f"/admin/orders/{order.id}/status", data={"status": "refunded"})

        self.assertEqual(db.session.get(Order, order.id).status, "preparing")


if __name__ == "__main__":
    unittest.main()
