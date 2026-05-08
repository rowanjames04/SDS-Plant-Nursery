import unittest

from tests.helpers import NurseryTestCase
from app import build_cart_summary, db, decimal_price, get_or_create_active_cart, load_catalog
from models import Cart, CartItem, Category, Plant, User, Wishlist


class Sprint1CatalogUserTests(NurseryTestCase):
    def test_user_passwords_are_hashed_and_checkable(self):
        user = self.make_user(password="correct-password")

        self.assertNotEqual(user.password_hash, "correct-password")
        self.assertTrue(user.check_password("correct-password"))
        self.assertFalse(user.check_password("wrong-password"))

    def test_register_creates_customer_account(self):
        response = self.client.post(
            "/register",
            data={
                "email": "new@example.com",
                "fullname": "New Customer",
                "password": "password123",
                "confirm-password": "password123",
            },
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 302)
        self.assertIsNotNone(User.query.filter_by(email="new@example.com").first())

    def test_load_catalog_returns_categories_species_varieties_and_plants(self):
        plant, _, _ = self.make_plant_with_pot()

        catalog = load_catalog()

        self.assertEqual([category.name for category in catalog["categories"]], ["Indoor Plants"])
        self.assertEqual(catalog["plants"][0]["id"], plant.id)
        self.assertEqual(catalog["plants"][0]["primary_image"], "plants/swiss-cheese-plant.jpg")

    def test_plants_page_filters_by_category_and_search_query(self):
        plant, _, _ = self.make_plant_with_pot(common_name="Swiss Cheese Plant")
        other_category = Category(name="Herbs")
        other = Plant(common_name="Sweet Basil", category_id=None)
        db.session.add_all([other_category, other])
        db.session.commit()

        response = self.client.get(f"/plants?category={plant.category_id}&q=Swiss")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Swiss Cheese Plant", response.data)
        self.assertNotIn(b"Sweet Basil", response.data)

    def test_active_cart_is_created_once_and_summarised(self):
        user = self.make_user()
        plant, pot, _ = self.make_plant_with_pot()

        cart = get_or_create_active_cart(user)
        second_lookup = get_or_create_active_cart(user)
        db.session.add(
            CartItem(
                cart_id=cart.id,
                plant_id=plant.id,
                pot_id=pot.id,
                quantity=3,
                unit_price_snapshot=decimal_price("12.50"),
                plant_name_snapshot=plant.common_name,
                pot_size_snapshot=pot.size,
                image_snapshot=plant.primary_image,
            )
        )
        db.session.commit()
        summary = build_cart_summary(db.session.get(Cart, cart.id))

        self.assertEqual(cart.id, second_lookup.id)
        self.assertEqual(summary["item_count"], 3)
        self.assertEqual(summary["subtotal"], decimal_price("37.50"))

    def test_wishlist_does_not_duplicate_existing_plant(self):
        user = self.make_user()
        plant, _, _ = self.make_plant_with_pot()
        self.login()

        self.client.post(f"/wishlist/add/{plant.id}")
        self.client.post(f"/wishlist/add/{plant.id}")

        self.assertEqual(Wishlist.query.filter_by(user_id=user.id, plant_id=plant.id).count(), 1)


if __name__ == "__main__":
    unittest.main()
