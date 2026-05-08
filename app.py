import os
import json
import math
import urllib.parse
import urllib.request
from collections import Counter
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData, inspect, text, func
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

try:
    import stripe
except ModuleNotFoundError:
    stripe = None


load_dotenv()
UPLOAD_FOLDER = 'static/images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
MAX_CONTENT_LENGTH = 5 * 1000 * 1000  # 5 MB limit for uploaded images
DEFAULT_DEV_SECRET_KEY = "dev-secret-key-change-me"
GOOGLE_MAPS_API_KEY_FILE = "google_maps_api_key.txt"
JILLIBY_CEMETERY_LATITUDE = -33.2610013
JILLIBY_CEMETERY_LONGITUDE = 151.3974672
LOCAL_DELIVERY_RADIUS_KM = Decimal("20.00")
LOCAL_DELIVERY_FEE = Decimal("60.00")
FREE_DELIVERY_PLANT_COUNT = 10


def load_google_maps_api_key():
    key_path = os.path.join(os.path.dirname(__file__), GOOGLE_MAPS_API_KEY_FILE)
    try:
        with open(key_path, "r", encoding="utf-8") as key_file:
            key = key_file.read().strip()
    except OSError:
        key = ""

    if key and key != "PUT-API-KEY-HERE":
        return key

    return os.getenv("GOOGLE_MAPS_API_KEY", "").strip()

app = Flask(__name__, instance_relative_config=True)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DB_URI', 'sqlite:///nursery.db')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY') or DEFAULT_DEV_SECRET_KEY
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
app.config['GOOGLE_MAPS_API_KEY'] = load_google_maps_api_key()
app.config['STRIPE_SECRET_KEY'] = os.getenv('STRIPE_SECRET_KEY', '').strip()
app.config['STRIPE_WEBHOOK_SECRET'] = os.getenv('STRIPE_WEBHOOK_SECRET', '').strip()
default_site_url = os.getenv('SITE_URL', '').strip()
if not default_site_url:
    render_hostname = os.getenv('RENDER_EXTERNAL_HOSTNAME', '').strip()
    default_site_url = f"https://{render_hostname}" if render_hostname else 'http://localhost:5000'
app.config['SITE_URL'] = default_site_url.rstrip('/')
if stripe is not None:
    stripe.api_key = app.config['STRIPE_SECRET_KEY'] or None

convention = {
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
}

db = SQLAlchemy(app, metadata=MetaData(naming_convention=convention))
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'


def utc_now():
    return datetime.now(UTC).replace(tzinfo=None)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

from models import Cart, CartItem, Category, Order, OrderItem, Plant, PlantPot, Pot, Species, User, UserAddress, Variety, Wishlist
from admin import admin_bp
app.register_blueprint(admin_bp)
    
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_image(file):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return filename
    return None

def load_catalog():
    categories = Category.query.order_by(Category.name).all()
    species = Species.query.order_by(Species.name).all()
    varieties = Variety.query.order_by(Variety.name).all()
    plants = Plant.query.order_by(Plant.common_name).all()

    category_map = {item.id: item.name for item in categories}
    species_map = {item.id: item.name for item in species}
    variety_map = {item.id: item.name for item in varieties}

    plant_rows = []
    for plant in plants:
        plant_rows.append({
            "id": plant.id,
            "common_name": plant.common_name,
            "scientific_name": plant.scientific_name,
            "category_name": category_map.get(plant.category_id),
            "species_name": species_map.get(plant.species_id),
            "variety_name": variety_map.get(plant.variety_id),
            "description": plant.description,
            "colour": plant.colour,
            "growth_width": plant.growth_width,
            "growth_height": plant.growth_height,
            "fragrant": plant.fragrant,
            "frost_sensitive": plant.frost_sensitive,
            "flowering_period": plant.flowering_period,
            "light_requirements": plant.light_requirements,
            "soil_requirements": plant.soil_requirements,
            "planting_advice": plant.planting_advice,
            "watering_needs": plant.watering_needs,
            "pruning_needs": plant.pruning_needs,
            "plant_pots": plant.plant_pots,
            "primary_image": plant.primary_image,
        })

    return {
        "categories": categories,
        "species": species,
        "varieties": varieties,
        "plants": plant_rows,
    }


def get_or_create_active_cart(user):
    cart = (
        Cart.query.filter_by(user_id=user.id, status="active")
        .order_by(Cart.updated_at.desc(), Cart.id.desc())
        .first()
    )
    if cart is None:
        cart = Cart(user_id=user.id)
        db.session.add(cart)
        db.session.flush()
    return cart


def decimal_price(value):
    if value is None:
        return Decimal("0.00")
    if isinstance(value, Decimal):
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def build_cart_summary(cart):
    items = []
    subtotal = Decimal("0.00")

    for item in cart.items:
        unit_price = decimal_price(item.unit_price_snapshot)
        line_total = unit_price * item.quantity
        subtotal += line_total
        items.append(
            {
                "id": item.id,
                "plant_id": item.plant_id,
                "pot_id": item.pot_id,
                "name": item.plant_name_snapshot,
                "pot_size": item.pot_size_snapshot,
                "image_filename": item.image_snapshot,
                "quantity": item.quantity,
                "unit_price": unit_price,
                "line_total": line_total,
                "plant": item.plant,
            }
        )

    return {
        "items": items,
        "subtotal": subtotal,
        "total": subtotal,
        "item_count": sum(item["quantity"] for item in items),
    }


def sync_order_with_cart(user, cart):
    order = (
        Order.query.filter_by(user_id=user.id, cart_id=cart.id, status="pending")
        .order_by(Order.updated_at.desc(), Order.id.desc())
        .first()
    )
    if order is None:
        order = Order(user_id=user.id, cart_id=cart.id)
        db.session.add(order)
        db.session.flush()

    order.items.clear()
    subtotal = Decimal("0.00")

    for cart_item in cart.items:
        line_total = decimal_price(cart_item.unit_price_snapshot) * cart_item.quantity
        subtotal += line_total
        order.items.append(
            OrderItem(
                plant_id=cart_item.plant_id,
                pot_id=cart_item.pot_id,
                quantity=cart_item.quantity,
                unit_price_snapshot=decimal_price(cart_item.unit_price_snapshot),
                plant_name_snapshot=cart_item.plant_name_snapshot,
                pot_size_snapshot=cart_item.pot_size_snapshot,
                image_snapshot=cart_item.image_snapshot,
            )
        )

    order.subtotal_amount = subtotal
    order.delivery_fee = Decimal("0.00")
    order.total_amount = subtotal
    order.payment_status = "pending"
    return order


def build_order_summary(order):
    items = []
    for item in order.items:
        unit_price = decimal_price(item.unit_price_snapshot)
        items.append(
            {
                "id": item.id,
                "plant_id": item.plant_id,
                "pot_id": item.pot_id,
                "name": item.plant_name_snapshot,
                "pot_size": item.pot_size_snapshot,
                "image_filename": item.image_snapshot,
                "quantity": item.quantity,
                "unit_price": unit_price,
                "line_total": unit_price * item.quantity,
            }
        )

    return {
        "items": items,
        "subtotal": decimal_price(order.subtotal_amount),
        "delivery_fee": decimal_price(order.delivery_fee),
        "total": decimal_price(order.total_amount),
        "item_count": sum(item["quantity"] for item in items),
    }


def get_place_component(components, component_type, use_short_name=False):
    for component in components:
        if component_type in component.get("types", []):
            key = "short_name" if use_short_name else "long_name"
            return component.get(key, "")
    return ""


def verified_address_from_place(place_id):
    api_key = app.config.get("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return None, "Google Maps address verification is not configured."

    params = urllib.parse.urlencode({
        "place_id": place_id,
        "fields": "address_components,formatted_address,geometry,place_id",
        "key": api_key,
    })
    url = f"https://maps.googleapis.com/maps/api/place/details/json?{params}"

    try:
        with urllib.request.urlopen(url, timeout=8) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, ValueError):
        return None, "We could not verify that address. Please try the search again."

    if payload.get("status") != "OK":
        return None, "Please choose a verified address from the search results."

    result = payload.get("result", {})
    components = result.get("address_components", [])
    street_number = get_place_component(components, "street_number")
    route = get_place_component(components, "route")
    line1 = " ".join(part for part in [street_number, route] if part).strip()
    city = (
        get_place_component(components, "locality")
        or get_place_component(components, "postal_town")
        or get_place_component(components, "sublocality")
        or get_place_component(components, "administrative_area_level_2")
    )
    state = get_place_component(components, "administrative_area_level_1", use_short_name=True)
    postal_code = get_place_component(components, "postal_code")
    country = get_place_component(components, "country")
    country_code = get_place_component(components, "country", use_short_name=True)
    line2 = get_place_component(components, "subpremise")
    location = result.get("geometry", {}).get("location", {})

    if not all([line1, city, state, postal_code, country, result.get("formatted_address")]):
        return None, "Please choose a complete street address from the search results."

    if country_code != "AU":
        return None, "Please choose an address in Australia."

    return {
        "line1": line1,
        "line2": line2,
        "city": city,
        "state": state,
        "postal_code": postal_code,
        "country": country,
        "formatted_address": result["formatted_address"],
        "google_place_id": result.get("place_id", place_id),
        "latitude": location.get("lat"),
        "longitude": location.get("lng"),
    }, None


def distance_km(lat1, lon1, lat2=JILLIBY_CEMETERY_LATITUDE, lon2=JILLIBY_CEMETERY_LONGITUDE):
    if None in (lat1, lon1, lat2, lon2):
        return None

    radius = 6371.0
    phi1 = math.radians(float(lat1))
    phi2 = math.radians(float(lat2))
    delta_phi = math.radians(float(lat2) - float(lat1))
    delta_lambda = math.radians(float(lon2) - float(lon1))
    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    return Decimal(str(radius * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))))).quantize(Decimal("0.01"))


def delivery_quote_for_address(address, plant_count):
    distance = distance_km(address.get("latitude"), address.get("longitude"))
    if distance is None:
        return None, None, "We could not calculate delivery distance for that address."
    if distance > LOCAL_DELIVERY_RADIUS_KM:
        return distance, None, "This address is outside our 20km delivery radius. Please email us for delivery options."
    if plant_count >= FREE_DELIVERY_PLANT_COUNT:
        return distance, Decimal("0.00"), None
    return distance, LOCAL_DELIVERY_FEE, None


def address_dict_from_user_address(address):
    return {
        "line1": address.line1,
        "line2": address.line2,
        "city": address.city,
        "state": address.state,
        "postal_code": address.postal_code,
        "country": address.country,
        "formatted_address": address.formatted_address,
        "google_place_id": address.google_place_id,
        "latitude": address.latitude,
        "longitude": address.longitude,
    }


def validate_cart_stock(cart):
    shortages = []
    for item in cart.items:
        if item.pot_id is None:
            shortages.append(f"{item.plant_name_snapshot} needs a pot size before checkout.")
            continue
        plant_pot = PlantPot.query.filter_by(plant_id=item.plant_id, pot_id=item.pot_id).first()
        if plant_pot is None:
            shortages.append(f"{item.plant_name_snapshot} is no longer available in that pot size.")
        elif plant_pot.stock_qty < item.quantity:
            shortages.append(
                f"Only {plant_pot.stock_qty} {item.plant_name_snapshot} "
                f"({item.pot_size_snapshot or plant_pot.pot.size}mm) left in stock."
            )
    return shortages


def sync_payment_pending_order(user, cart, delivery_method, address=None, delivery_fee=Decimal("0.00"), delivery_distance=None):
    order = (
        Order.query.filter_by(user_id=user.id, cart_id=cart.id, status="payment_pending")
        .order_by(Order.updated_at.desc(), Order.id.desc())
        .first()
    )
    if order is None:
        order = Order(user_id=user.id, cart_id=cart.id, status="payment_pending")
        db.session.add(order)
        db.session.flush()

    order.items.clear()
    order.payment_status = "unpaid"
    order.delivery_method = delivery_method
    order.delivery_fee = delivery_fee
    order.delivery_distance_km = delivery_distance
    order.stripe_payment_intent_id = None
    subtotal = Decimal("0.00")

    if address:
        order.delivery_line1 = address["line1"]
        order.delivery_line2 = address.get("line2")
        order.delivery_city = address["city"]
        order.delivery_state = address["state"]
        order.delivery_postal_code = address["postal_code"]
        order.delivery_country = address["country"]
        order.delivery_formatted_address = address["formatted_address"]
        order.delivery_google_place_id = address["google_place_id"]
        order.delivery_latitude = address.get("latitude")
        order.delivery_longitude = address.get("longitude")
    else:
        order.delivery_line1 = None
        order.delivery_line2 = None
        order.delivery_city = None
        order.delivery_state = None
        order.delivery_postal_code = None
        order.delivery_country = None
        order.delivery_formatted_address = None
        order.delivery_google_place_id = None
        order.delivery_latitude = None
        order.delivery_longitude = None

    for cart_item in cart.items:
        unit_price = decimal_price(cart_item.unit_price_snapshot)
        subtotal += unit_price * cart_item.quantity
        order.items.append(
            OrderItem(
                plant_id=cart_item.plant_id,
                pot_id=cart_item.pot_id,
                quantity=cart_item.quantity,
                unit_price_snapshot=unit_price,
                plant_name_snapshot=cart_item.plant_name_snapshot,
                pot_size_snapshot=cart_item.pot_size_snapshot,
                image_snapshot=cart_item.image_snapshot,
            )
        )

    order.subtotal_amount = subtotal
    order.delivery_fee = delivery_fee
    order.total_amount = subtotal + delivery_fee
    order.updated_at = utc_now()
    cart.updated_at = utc_now()
    return order


def session_value(session, key, default=None):
    if hasattr(session, "get"):
        return session.get(key, default)
    return getattr(session, key, default)


def fulfill_stripe_checkout_session(session_id, session=None):
    if not session_id:
        raise ValueError("Missing Stripe Checkout Session ID.")
    if stripe is None:
        raise RuntimeError("The stripe Python package is not installed.")

    if session is None:
        session = stripe.checkout.Session.retrieve(session_id)

    payment_status = session_value(session, "payment_status")
    if payment_status != "paid":
        return None

    metadata = session_value(session, "metadata", {}) or {}
    order_id = metadata.get("order_id") if hasattr(metadata, "get") else getattr(metadata, "order_id", None)
    if not order_id:
        raise ValueError("Stripe session is missing order metadata.")

    order = db.session.get(Order, int(order_id))
    if order is None:
        raise ValueError("Order for Stripe session was not found.")

    if order.payment_status == "paid":
        return order

    stock_errors = []
    stock_rows = []
    for item in order.items:
        plant_pot = PlantPot.query.filter_by(plant_id=item.plant_id, pot_id=item.pot_id).first()
        if plant_pot is None:
            stock_errors.append(f"{item.plant_name_snapshot} is no longer available in that pot size.")
        elif plant_pot.stock_qty < item.quantity:
            stock_errors.append(
                f"Only {plant_pot.stock_qty} {item.plant_name_snapshot} "
                f"({item.pot_size_snapshot or plant_pot.pot.size}mm) left in stock."
            )
        else:
            stock_rows.append((plant_pot, item.quantity))

    if stock_errors:
        order.payment_status = "failed"
        db.session.commit()
        raise ValueError(" ".join(stock_errors))

    for plant_pot, quantity in stock_rows:
        plant_pot.stock_qty -= quantity

    order.stripe_checkout_session_id = session_value(session, "id", session_id)
    order.stripe_payment_intent_id = session_value(session, "payment_intent")
    order.payment_status = "paid"
    order.status = "preparing"
    order.updated_at = utc_now()
    if order.cart:
        order.cart.status = "ordered"
        order.cart.updated_at = utc_now()
    db.session.commit()
    return order


def mark_stripe_checkout_session_failed(session):
    metadata = session_value(session, "metadata", {}) or {}
    order_id = metadata.get("order_id") if hasattr(metadata, "get") else getattr(metadata, "order_id", None)
    if not order_id:
        return None

    order = db.session.get(Order, int(order_id))
    if order is None or order.payment_status == "paid":
        return order

    order.stripe_checkout_session_id = session_value(session, "id", order.stripe_checkout_session_id)
    order.stripe_payment_intent_id = session_value(session, "payment_intent")
    order.payment_status = "failed"
    order.updated_at = utc_now()
    if order.cart:
        order.cart.status = "active"
        order.cart.updated_at = utc_now()
    db.session.commit()
    return order


def expire_stripe_checkout_session(session):
    metadata = session_value(session, "metadata", {}) or {}
    order_id = metadata.get("order_id") if hasattr(metadata, "get") else getattr(metadata, "order_id", None)
    if not order_id:
        return None

    order = db.session.get(Order, int(order_id))
    if order is None or order.payment_status == "paid":
        return order

    order.stripe_checkout_session_id = session_value(session, "id", order.stripe_checkout_session_id)
    order.payment_status = "expired"
    order.updated_at = utc_now()
    if order.cart:
        order.cart.status = "active"
        order.cart.updated_at = utc_now()
    db.session.commit()
    return order


def ensure_active_stripe_config():
    if stripe is None:
        raise RuntimeError("The stripe Python package is not installed. Run pip install -r requirements.txt.")
    if not app.config.get("STRIPE_SECRET_KEY"):
        raise RuntimeError("Stripe is not configured. Add STRIPE_SECRET_KEY to the environment.")


def create_stripe_checkout_session_for_order(order):
    ensure_active_stripe_config()
    from payments.checkout import create_checkout_session

    session = create_checkout_session(order)
    order.stripe_checkout_session_id = session_value(session, "id")
    if order.cart:
        order.cart.updated_at = utc_now()
    return session


def get_active_cart(user):
    return (
        Cart.query.filter_by(user_id=user.id, status="active")
        .order_by(Cart.updated_at.desc(), Cart.id.desc())
        .first()
    )


def get_header_cart_summary():
    if not current_user.is_authenticated:
        return {
            "header_cart_item_count": 0,
            "header_cart_total": Decimal("0.00"),
        }

    cart = get_active_cart(current_user)
    if cart is None:
        return {
            "header_cart_item_count": 0,
            "header_cart_total": Decimal("0.00"),
        }

    summary = build_cart_summary(cart)
    return {
        "header_cart_item_count": summary["item_count"],
        "header_cart_total": summary["total"],
    }


def repair_legacy_user_table():
    database_uri = app.config["SQLALCHEMY_DATABASE_URI"]
    if not database_uri.startswith("sqlite"):
        return

    inspector = inspect(db.engine)
    if "user" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("user")}
    has_legacy_shape = "id" not in columns and "password" in columns
    if not has_legacy_shape:
        return

    with db.engine.begin() as connection:
        connection.execute(text("""
            CREATE TABLE user__migration (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                email VARCHAR(120) NOT NULL UNIQUE,
                full_name VARCHAR(100) NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                is_staff BOOLEAN NOT NULL DEFAULT 0
            )
        """))
        connection.execute(text("""
            INSERT INTO user__migration (email, full_name, password_hash, is_staff)
            SELECT email, full_name, password, COALESCE(is_staff, 0)
            FROM user
        """))
        connection.execute(text("DROP TABLE user"))
        connection.execute(text("ALTER TABLE user__migration RENAME TO user"))


def repair_legacy_plant_table():
    database_uri = app.config["SQLALCHEMY_DATABASE_URI"]
    if not database_uri.startswith("sqlite"):
        return

    inspector = inspect(db.engine)
    if "plant" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("plant")}
    if "images" in columns:
        return

    with db.engine.begin() as connection:
        connection.execute(text("ALTER TABLE plant ADD COLUMN images JSON"))

        if "image_filename" in columns:
            legacy_images = connection.execute(text("""
                SELECT id, image_filename
                FROM plant
                WHERE image_filename IS NOT NULL
                  AND image_filename != ''
            """)).mappings()

            for row in legacy_images:
                connection.execute(
                    text("UPDATE plant SET images = :images WHERE id = :id"),
                    {"id": row["id"], "images": json.dumps([row["image_filename"]])},
                )


def repair_checkout_tables():
    database_uri = app.config["SQLALCHEMY_DATABASE_URI"]
    if not database_uri.startswith("sqlite"):
        return

    inspector = inspect(db.engine)
    tables = set(inspector.get_table_names())
    if not {"cart_item", "order", "order_item"}.issubset(tables):
        return

    table_columns = {
        table: {column["name"] for column in inspector.get_columns(table)}
        for table in ("cart_item", "order", "order_item")
    }
    column_specs = {
        "cart_item": {
            "pot_id": "INTEGER",
            "pot_size_snapshot": "INTEGER",
        },
        "order": {
            "delivery_fee": "NUMERIC(10, 2) NOT NULL DEFAULT 0",
            "delivery_method": "VARCHAR(30)",
            "delivery_distance_km": "NUMERIC(8, 2)",
            "delivery_line1": "VARCHAR(255)",
            "delivery_line2": "VARCHAR(255)",
            "delivery_city": "VARCHAR(120)",
            "delivery_state": "VARCHAR(120)",
            "delivery_postal_code": "VARCHAR(20)",
            "delivery_country": "VARCHAR(120)",
            "delivery_formatted_address": "VARCHAR(500)",
            "delivery_google_place_id": "VARCHAR(255)",
            "delivery_latitude": "FLOAT",
            "delivery_longitude": "FLOAT",
        },
        "order_item": {
            "pot_id": "INTEGER",
            "pot_size_snapshot": "INTEGER",
        },
    }

    with db.engine.begin() as connection:
        for table, specs in column_specs.items():
            for column_name, column_type in specs.items():
                if column_name not in table_columns[table]:
                    connection.execute(text(f'ALTER TABLE "{table}" ADD COLUMN {column_name} {column_type}'))

        for table in ("cart_item", "order_item"):
            connection.execute(text(f"""
                UPDATE {table}
                SET pot_id = (
                    SELECT plant_pot.pot_id
                    FROM plant_pot
                    JOIN pot ON pot.id = plant_pot.pot_id
                    WHERE plant_pot.plant_id = {table}.plant_id
                    ORDER BY pot.size
                    LIMIT 1
                )
                WHERE pot_id IS NULL
            """))
            connection.execute(text(f"""
                UPDATE {table}
                SET pot_size_snapshot = (
                    SELECT pot.size
                    FROM pot
                    WHERE pot.id = {table}.pot_id
                )
                WHERE pot_size_snapshot IS NULL
                  AND pot_id IS NOT NULL
            """))


with app.app_context():
    repair_legacy_user_table()
    repair_legacy_plant_table()
    # Create any missing tables for a fresh local SQLite database.
    db.create_all()
    repair_checkout_tables()


@app.context_processor
def inject_header_cart_summary():
    return get_header_cart_summary()
    
@app.route("/")
def home():
    catalog = load_catalog()
    return render_template(
        'Home.html',
        categories=catalog["categories"],
        species=catalog["species"],
        varieties=catalog["varieties"],
        plants=catalog["plants"],
    )



@app.route("/plants")
def plants_index():
    active_categories = set(request.args.getlist('category', type=int))
    search_query = request.args.get('q', '').strip()

    categories = Category.query.order_by(Category.name).all()
    species_list = Species.query.order_by(Species.name).all()
    varieties = Variety.query.order_by(Variety.name).all()

    category_map = {c.id: c.name for c in categories}
    species_map = {s.id: s.name for s in species_list}
    variety_map = {v.id: v.name for v in varieties}

    all_plants = Plant.query.all()
    cat_counts = Counter(p.category_id for p in all_plants if p.category_id)

    min_prices = dict(
        db.session.query(PlantPot.plant_id, func.min(PlantPot.price))
        .group_by(PlantPot.plant_id)
        .all()
    )

    q = Plant.query
    if active_categories:
        q = q.filter(Plant.category_id.in_(active_categories))
    if search_query:
        like = f'%{search_query}%'
        q = q.filter(
            db.or_(
                Plant.common_name.ilike(like),
                Plant.scientific_name.ilike(like),
            )
        )

    plant_rows = []
    for plant in q.order_by(Plant.common_name).all():
        plant_rows.append({
            "id": plant.id,
            "common_name": plant.common_name,
            "scientific_name": plant.scientific_name,
            "category_name": category_map.get(plant.category_id),
            "species_name": species_map.get(plant.species_id),
            "variety_name": variety_map.get(plant.variety_id),
            "description": plant.description,
            "min_price": min_prices.get(plant.id),
            "primary_image": plant.primary_image,
        })

    def toggle_category_url(active_cats, cat_id):
        cats = set(active_cats)
        if cat_id in cats:
            cats.discard(cat_id)
        else:
            cats.add(cat_id)
        parts = []
        if search_query:
            parts.append(f'q={urllib.parse.quote_plus(search_query)}')
        parts.extend(f'category={c}' for c in sorted(cats))
        return url_for('plants_index') + ('?' + '&'.join(parts) if parts else '')

    return render_template(
        "plants.html",
        plants=plant_rows,
        categories=categories,
        species=species_list,
        varieties=varieties,
        cat_counts=cat_counts,
        active_categories=active_categories,
        active_category_ids=sorted(active_categories),
        toggle_category_url=toggle_category_url,
        search_query=search_query,
        total_plants=len(all_plants),
    )

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        place_id = request.form.get("google_place_id", "").strip()
        if not place_id:
            flash("Please choose an address from the search results.", "error")
            return redirect(url_for("profile"))

        verified_address, error = verified_address_from_place(place_id)
        if error:
            flash(error, "error")
            return redirect(url_for("profile"))

        verified_address["line2"] = request.form.get("line2", "").strip()
        verified_address["is_default"] = True

        if current_user.address is None:
            current_user.address = UserAddress(**verified_address)
        else:
            for field, value in verified_address.items():
                setattr(current_user.address, field, value)

        db.session.commit()
        flash("Your default address has been saved.", "success")
        return redirect(url_for("profile"))

    user_orders = (
        Order.query.filter_by(user_id=current_user.id)
        .filter(Order.payment_status == "paid")
        .order_by(Order.created_at.desc())
        .all()
    )
    return render_template(
        'profile.html',
        user=current_user,
        address=current_user.address,
        orders=user_orders,
        google_maps_api_key=app.config.get("GOOGLE_MAPS_API_KEY"),
    )

@app.route("/orders")
@login_required
def orders():
    user_orders = (
        Order.query.filter_by(user_id=current_user.id)
        .filter(Order.payment_status == "paid")
        .order_by(Order.created_at.desc())
        .all()
    )
    return render_template('orders.html', orders=user_orders)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            flash(f'Welcome back, {user.full_name}!', 'success')
            next_page = request.form.get('next') or request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('home'))
        else:
            flash('Invalid email or password', 'error')

    return render_template('Login.html')

@app.route("/logout", methods=['GET', 'POST'])
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.route("/wishlist")
@login_required
def wishlist():
    wishlist_items = Wishlist.query.filter_by(user_id=current_user.id).order_by(Wishlist.created_at.desc()).all()
    return render_template(
        "wishlist.html",
        wishlist_items=wishlist_items,
    )


@app.route("/wishlist/add/<int:plant_id>", methods=["POST"])
@login_required
def add_to_wishlist(plant_id):
    # Check if already in wishlist
    existing = Wishlist.query.filter_by(user_id=current_user.id, plant_id=plant_id).first()
    if existing:
        flash("Plant is already in your wishlist.", "info")
    else:
        wishlist_item = Wishlist(user_id=current_user.id, plant_id=plant_id)
        db.session.add(wishlist_item)
        db.session.commit()
        flash("Added to wishlist!", "success")

    next_url = request.form.get("next")
    if next_url:
        return redirect(next_url)
    return redirect(url_for("wishlist"))


@app.route("/wishlist/remove/<int:plant_id>", methods=["POST"])
@login_required
def remove_from_wishlist(plant_id):
    wishlist_item = Wishlist.query.filter_by(user_id=current_user.id, plant_id=plant_id).first_or_404()
    db.session.delete(wishlist_item)
    db.session.commit()
    flash("Removed from wishlist.", "info")

    next_url = request.form.get("next")
    if next_url:
        return redirect(next_url)
    return redirect(url_for("wishlist"))

@app.route("/cart")
@login_required
def cart():
    cart = get_or_create_active_cart(current_user)
    summary = build_cart_summary(cart)
    return render_template(
        "cart.html",
        cart=cart,
        cart_items=summary["items"],
        cart_subtotal=summary["subtotal"],
        cart_total=summary["total"],
        cart_item_count=summary["item_count"],
    )


@app.route("/cart/add", methods=["POST"])
@login_required
def add_to_cart():
    plant_id = request.form.get("plant_id", type=int)
    pot_id = request.form.get("pot_id", type=int)
    quantity = request.form.get("quantity", default=1, type=int)
    quantity = max(quantity or 1, 1)

    plant_pot = PlantPot.query.filter_by(plant_id=plant_id, pot_id=pot_id).first_or_404()
    plant = plant_pot.plant
    cart = get_or_create_active_cart(current_user)
    existing_item = CartItem.query.filter_by(cart_id=cart.id, plant_id=plant.id, pot_id=pot_id).first()

    cart_quantity = existing_item.quantity if existing_item else 0
    if cart_quantity + quantity > plant_pot.stock_qty:
        flash(f"Only {plant_pot.stock_qty} {plant.common_name} in {plant_pot.pot.size}mm pots are available.", "error")
        next_url = request.form.get("next")
        if next_url:
            return redirect(next_url)
        return redirect(url_for("plant_detail", id=plant.id))

    if existing_item:
        existing_item.quantity += quantity
        existing_item.unit_price_snapshot = decimal_price(plant_pot.price)
        existing_item.plant_name_snapshot = plant.common_name
        existing_item.pot_size_snapshot = plant_pot.pot.size
        existing_item.image_snapshot = plant.primary_image
    else:
        db.session.add(
            CartItem(
                cart_id=cart.id,
                plant_id=plant.id,
                pot_id=plant_pot.pot_id,
                quantity=quantity,
                unit_price_snapshot=decimal_price(plant_pot.price),
                plant_name_snapshot=plant.common_name,
                pot_size_snapshot=plant_pot.pot.size,
                image_snapshot=plant.primary_image,
            )
        )

    cart.updated_at = utc_now()
    db.session.commit()
    flash(f"{plant.common_name} added to your cart.", "success")

    next_url = request.form.get("next")
    if next_url:
        return redirect(next_url)
    return redirect(url_for("cart"))


@app.route("/cart/items/<int:item_id>/update", methods=["POST"])
@login_required
def update_cart_item(item_id):
    cart = get_or_create_active_cart(current_user)
    item = CartItem.query.filter_by(id=item_id, cart_id=cart.id).first_or_404()
    action = request.form.get("action", "set")

    if action == "remove":
        db.session.delete(item)
        flash("Item removed from your cart.", "success")
    elif action == "increase":
        item.quantity += 1
    elif action == "decrease":
        item.quantity -= 1
        if item.quantity <= 0:
            db.session.delete(item)
            flash("Item removed from your cart.", "success")
    else:
        raw_quantity = request.form.get("quantity", "1")
        try:
            quantity = int(raw_quantity)
        except (TypeError, ValueError):
            quantity = 1

        if quantity <= 0:
            db.session.delete(item)
            flash("Item removed from your cart.", "success")
        else:
            item.quantity = quantity

    cart.updated_at = utc_now()
    db.session.commit()
    return redirect(url_for("cart"))


@app.route("/cart/update", methods=["POST"])
@login_required
def update_cart():
    cart = get_or_create_active_cart(current_user)
    items = CartItem.query.filter_by(cart_id=cart.id).all()
    item_map = {item.id: item for item in items}

    removed_any = False
    changed_any = False

    for key, raw_value in request.form.items():
        if not key.startswith("quantity_"):
            continue

        try:
            item_id = int(key.split("_", 1)[1])
        except (TypeError, ValueError):
            continue

        item = item_map.get(item_id)
        if item is None:
            continue

        try:
            quantity = int(raw_value)
        except (TypeError, ValueError):
            quantity = item.quantity

        if quantity <= 0:
            db.session.delete(item)
            removed_any = True
            changed_any = True
        elif quantity != item.quantity:
            item.quantity = quantity
            changed_any = True

    if changed_any:
        cart.updated_at = utc_now()
        db.session.commit()
        if removed_any:
            flash("Cart updated. Items with zero quantity were removed.", "success")
        else:
            flash("Your cart has been updated.", "success")
    else:
        flash("No changes were made to your cart.", "info")

    return redirect(url_for("cart"))


@app.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    cart = get_or_create_active_cart(current_user)
    if not cart.items:
        flash("Your cart is empty.", "info")
        return redirect(url_for("cart"))

    summary = build_cart_summary(cart)
    stock_errors = validate_cart_stock(cart)
    if stock_errors:
        for error in stock_errors:
            flash(error, "error")
        return redirect(url_for("cart"))

    saved_address_quote = None
    if current_user.address:
        saved_address = address_dict_from_user_address(current_user.address)
        distance, fee, error = delivery_quote_for_address(saved_address, summary["item_count"])
        saved_address_quote = {
            "distance": distance,
            "fee": fee,
            "error": error,
        }

    if request.method == "POST":
        delivery_method = request.form.get("delivery_method", "delivery")
        address = None
        delivery_fee = Decimal("0.00")
        delivery_distance = None

        if delivery_method == "pickup":
            pass
        elif delivery_method == "delivery":
            use_saved_address = request.form.get("use_saved_address") == "1"
            if use_saved_address:
                if current_user.address is None:
                    flash("Please add a delivery address before placing your order.", "error")
                    return redirect(url_for("checkout"))
                address = address_dict_from_user_address(current_user.address)
            else:
                place_id = request.form.get("google_place_id", "").strip()
                if not place_id:
                    flash("Please choose a verified delivery address from the search results.", "error")
                    return redirect(url_for("checkout"))
                address, error = verified_address_from_place(place_id)
                if error:
                    flash(error, "error")
                    return redirect(url_for("checkout"))
                address["line2"] = request.form.get("line2", "").strip()

                if request.form.get("save_address") == "1":
                    address_to_save = dict(address)
                    address_to_save["is_default"] = True
                    if current_user.address is None:
                        current_user.address = UserAddress(**address_to_save)
                    else:
                        for field, value in address_to_save.items():
                            setattr(current_user.address, field, value)

            delivery_distance, delivery_fee, delivery_error = delivery_quote_for_address(address, summary["item_count"])
            if delivery_error:
                flash(delivery_error, "error")
                return redirect(url_for("checkout"))
        else:
            flash("Please choose delivery or pickup.", "error")
            return redirect(url_for("checkout"))

        order = sync_payment_pending_order(
            current_user,
            cart,
            delivery_method,
            address=address,
            delivery_fee=delivery_fee,
            delivery_distance=delivery_distance,
        )
        try:
            session = create_stripe_checkout_session_for_order(order)
        except Exception as error:
            db.session.rollback()
            flash(f"We could not start Stripe Checkout: {error}", "error")
            return redirect(url_for("checkout"))

        db.session.commit()
        return redirect(session_value(session, "url"))

    return render_template(
        "checkout/checkout.html",
        cart=cart,
        checkout_items=summary["items"],
        checkout_subtotal=summary["subtotal"],
        checkout_total=summary["total"],
        checkout_item_count=summary["item_count"],
        delivery_fee=LOCAL_DELIVERY_FEE,
        free_delivery_plant_count=FREE_DELIVERY_PLANT_COUNT,
        local_delivery_radius_km=LOCAL_DELIVERY_RADIUS_KM,
        jilliby_cemetery_latitude=JILLIBY_CEMETERY_LATITUDE,
        jilliby_cemetery_longitude=JILLIBY_CEMETERY_LONGITUDE,
        saved_address=current_user.address,
        saved_address_quote=saved_address_quote,
        google_maps_api_key=app.config.get("GOOGLE_MAPS_API_KEY"),
    )


@app.route("/checkout/success")
@login_required
def checkout_success():
    session_id = request.args.get("session_id", "").strip()
    if not session_id:
        flash("Stripe did not return a checkout session. Please try again.", "error")
        return redirect(url_for("checkout"))
    if stripe is None:
        flash("Stripe support is not installed on this environment.", "error")
        return redirect(url_for("checkout"))

    try:
        session = stripe.checkout.Session.retrieve(session_id)
        metadata = session_value(session, "metadata", {}) or {}
        order_id = metadata.get("order_id") if hasattr(metadata, "get") else getattr(metadata, "order_id", None)
        order = Order.query.filter_by(id=int(order_id), user_id=current_user.id).first() if order_id else None
        if order is None:
            flash("That Stripe checkout session does not belong to your account.", "error")
            return redirect(url_for("checkout"))
        order = fulfill_stripe_checkout_session(session_id, session=session)
    except Exception as error:
        db.session.rollback()
        flash(f"We could not confirm your payment yet: {error}", "error")
        return redirect(url_for("checkout"))

    if order is None:
        flash("Payment has not completed yet. Please return to checkout and try again.", "error")
        return redirect(url_for("checkout"))

    summary = build_order_summary(order)
    return render_template(
        "checkout/success.html",
        order=order,
        order_summary=summary,
    )


@app.route("/checkout/cancel")
@login_required
def checkout_cancel():
    flash("Stripe Checkout was cancelled. Your cart has been preserved.", "error")
    return render_template("checkout/cancel.html")


@app.route("/stripe/webhook", methods=["POST"])
def stripe_webhook():
    if stripe is None:
        return "The stripe Python package is not installed.", 400

    webhook_secret = app.config.get("STRIPE_WEBHOOK_SECRET")
    if not webhook_secret:
        return "Stripe webhook secret is not configured.", 400

    payload = request.get_data()
    sig_header = request.headers.get("Stripe-Signature", "")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except ValueError:
        return "Invalid payload.", 400
    except stripe.error.SignatureVerificationError:
        return "Invalid signature.", 400

    event_type = event.get("type")
    session = event.get("data", {}).get("object", {})
    try:
        if event_type in ("checkout.session.completed", "checkout.session.async_payment_succeeded"):
            fulfill_stripe_checkout_session(session_value(session, "id"), session=session)
        elif event_type == "checkout.session.async_payment_failed":
            mark_stripe_checkout_session_failed(session)
        elif event_type == "checkout.session.expired":
            expire_stripe_checkout_session(session)
    except Exception:
        db.session.rollback()
        return "Webhook handling failed.", 400

    return "", 200


@app.route("/orders/<int:order_id>/confirmation")
@login_required
def order_confirmation(order_id):
    if current_user.is_staff:
        order = db.get_or_404(Order, order_id)
    else:
        order = Order.query.filter_by(id=order_id, user_id=current_user.id).first_or_404()
    if order.payment_status != "paid":
        flash("That order has not been paid for yet. Please complete checkout first.", "error")
        return redirect(url_for("checkout"))
    summary = build_order_summary(order)
    return render_template(
        "order_confirmation.html",
        order=order,
        order_items=summary["items"],
        order_subtotal=summary["subtotal"],
        order_delivery_fee=summary["delivery_fee"],
        order_total=summary["total"],
        order_item_count=summary["item_count"],
    )

@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        full_name = request.form.get('fullname') or request.form.get('full_name')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm-password') or request.form.get('confirm_password')

        if not email or not full_name or not password:
            flash('All fields are required', 'error')
            return render_template('Register.html')

        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('Register.html')

        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('Register.html')

        user = User(email=email, full_name=full_name)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('Account created! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('Register.html')


@app.route("/plants/<int:id>")
def plant_detail(id):
    plant = db.get_or_404(Plant, id)
    category = db.session.get(Category, plant.category_id) if plant.category_id else None
    species = db.session.get(Species, plant.species_id) if plant.species_id else None
    variety = db.session.get(Variety, plant.variety_id) if plant.variety_id else None
    plant_pots = PlantPot.query.filter_by(plant_id=id).order_by(PlantPot.pot_id).all()
    return render_template(
        'plant_detail.html',
        plant=plant,
        category=category,
        species=species,
        variety=variety,
        plant_pots=plant_pots,
        default_quantity=1,
    )
