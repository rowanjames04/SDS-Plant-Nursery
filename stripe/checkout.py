"""Stripe Checkout Session creation."""

import stripe
from app import app
from models import PlantPot


def create_checkout_session(order):
    """Create a Stripe Checkout Session for the given order.

    Args:
        order: Order model instance with items

    Returns:
        stripe.checkout.Session: The created checkout session
    """
    line_items = []

    for item in order.items:
        # Stripe expects amounts in cents (smallest currency unit)
        unit_amount = int(float(item.unit_price_snapshot) * 100)

        # Build image URL if available
        image_url = None
        if item.image_snapshot:
            base_url = app.config.get('SITE_URL', 'http://localhost:5000').rstrip('/')
            image_url = f'{base_url}/static/images/{item.image_snapshot}'

        line_items.append({
            'price_data': {
                'currency': 'aud',
                'product_data': {
                    'name': item.plant_name_snapshot,
                    'images': [image_url] if image_url else None,
                },
                'unit_amount': unit_amount,
            },
            'quantity': item.quantity,
        })

    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=line_items,
        mode='payment',
        success_url=f"{app.config.get('SITE_URL', 'http://localhost:5000').rstrip('/')}/checkout/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{app.config.get('SITE_URL', 'http://localhost:5000').rstrip('/')}/checkout/cancel",
        metadata={
            'order_id': str(order.id),
        },
    )

    return session
