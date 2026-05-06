"""Stripe Checkout Session creation."""

from decimal import Decimal, ROUND_HALF_UP

import stripe

from app import app, decimal_price


def amount_to_cents(amount):
    decimal_amount = decimal_price(amount)
    return int((decimal_amount * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def site_url():
    return app.config.get("SITE_URL", "http://127.0.0.1:5000").rstrip("/")


def create_checkout_session(order):
    line_items = []
    base_url = site_url()

    for item in order.items:
        product_data = {
            "name": item.plant_name_snapshot,
        }
        if item.image_snapshot:
            product_data["images"] = [f"{base_url}/static/images/{item.image_snapshot}"]

        line_items.append(
            {
                "price_data": {
                    "currency": "aud",
                    "product_data": product_data,
                    "unit_amount": amount_to_cents(item.unit_price_snapshot),
                },
                "quantity": item.quantity,
            }
        )

    if decimal_price(order.delivery_fee) > Decimal("0.00"):
        line_items.append(
            {
                "price_data": {
                    "currency": "aud",
                    "product_data": {
                        "name": "Local delivery",
                    },
                    "unit_amount": amount_to_cents(order.delivery_fee),
                },
                "quantity": 1,
            }
        )

    return stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=line_items,
        mode="payment",
        customer_email=order.user.email,
        success_url=f"{base_url}/checkout/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{base_url}/checkout/cancel",
        metadata={
            "order_id": str(order.id),
            "cart_id": str(order.cart_id),
            "user_id": str(order.user_id),
        },
    )
