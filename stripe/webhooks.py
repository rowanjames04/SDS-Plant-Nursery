"""Stripe webhook event handling."""

import stripe
from app import app, db
from models import Order


def handle_webhook_event(payload, sig_header):
    """Handle incoming Stripe webhook events.

    Args:
        payload: Raw request body bytes
        sig_header: Stripe-Signature header value

    Returns:
        stripe.Event: The constructed event

    Raises:
        ValueError: If payload or signature is invalid
    """
    webhook_secret = app.config.get('STRIPE_WEBHOOK_SECRET')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError as e:
        raise ValueError('Invalid payload') from e
    except stripe.error.SignatureVerificationError as e:
        raise ValueError('Invalid signature') from e

    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        handle_checkout_session_completed(session)

    return event


def handle_checkout_session_completed(session):
    """Handle checkout.session.completed event.

    Updates the order with payment confirmation and marks cart as completed.

    Args:
        session: Stripe checkout session object
    """
    order_id = session.get('metadata', {}).get('order_id')

    if not order_id:
        return

    order = Order.query.get(int(order_id))
    if not order:
        return

    # Update order with Stripe payment info
    order.stripe_checkout_session_id = session['id']
    order.stripe_payment_intent_id = session.get('payment_intent')
    order.payment_status = 'paid'
    order.status = 'confirmed'

    # Mark the cart as completed
    if order.cart:
        order.cart.status = 'completed'

    db.session.commit()
