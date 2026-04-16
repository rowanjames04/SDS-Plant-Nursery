import os
from datetime import datetime
from decimal import Decimal
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData, inspect, text
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from dotenv import load_dotenv
from werkzeug.utils import secure_filename


load_dotenv()
UPLOAD_FOLDER = 'static/images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
MAX_CONTENT_LENGTH = 16 * 1000 * 1000  # 16 MB lmit for uploaded images
DEFAULT_DEV_SECRET_KEY = "dev-secret-key-change-me"

app = Flask(__name__, instance_relative_config=True)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DB_URI', 'sqlite:///nursery.db')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY') or DEFAULT_DEV_SECRET_KEY
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

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

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

from models import Cart, CartItem, Category, Order, OrderItem, Plant, PlantPot, Pot, Species, User, Variety
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
        return value.quantize(Decimal("0.01"))
    return Decimal(str(value)).quantize(Decimal("0.01"))


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
                "name": item.plant_name_snapshot,
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
                quantity=cart_item.quantity,
                unit_price_snapshot=decimal_price(cart_item.unit_price_snapshot),
                plant_name_snapshot=cart_item.plant_name_snapshot,
                image_snapshot=cart_item.image_snapshot,
            )
        )

    order.subtotal_amount = subtotal
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
                "name": item.plant_name_snapshot,
                "image_filename": item.image_snapshot,
                "quantity": item.quantity,
                "unit_price": unit_price,
                "line_total": unit_price * item.quantity,
            }
        )

    return {
        "items": items,
        "subtotal": decimal_price(order.subtotal_amount),
        "total": decimal_price(order.total_amount),
        "item_count": sum(item["quantity"] for item in items),
    }


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


with app.app_context():
    repair_legacy_user_table()
    # Create any missing tables for a fresh local SQLite database.
    db.create_all()


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
    catalog = load_catalog()
    return render_template(
        "plants.html",
        plants=catalog["plants"],
        categories=catalog["categories"],
        species=catalog["species"],
        varieties=catalog["varieties"],
    )

@app.route("/profile")
@login_required
def profile():
    return render_template('profile.html', user=current_user)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            next_page = request.form.get('next') or request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('home'))
        else:
            flash('Invalid email or password', 'error')

    return render_template('Login.html')

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route("/wishlist")
@login_required
def wishlist():
    return render_template(
        "wishlist.html",
        wishlist_items=[],
    )

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
    existing_item = CartItem.query.filter_by(cart_id=cart.id, plant_id=plant.id).first()

    if existing_item:
        existing_item.quantity += quantity
        existing_item.unit_price_snapshot = decimal_price(plant_pot.price)
        existing_item.plant_name_snapshot = plant.common_name
        existing_item.image_snapshot = plant_pot.image_filename
    else:
        db.session.add(
            CartItem(
                cart_id=cart.id,
                plant_id=plant.id,
                quantity=quantity,
                unit_price_snapshot=decimal_price(plant_pot.price),
                plant_name_snapshot=plant.common_name,
                image_snapshot=plant_pot.image_filename,
            )
        )

    cart.updated_at = datetime.utcnow()
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

    cart.updated_at = datetime.utcnow()
    db.session.commit()
    return redirect(url_for("cart"))


@app.route("/checkout")
@login_required
def checkout():
    cart = get_or_create_active_cart(current_user)
    if not cart.items:
        flash("Your cart is empty.", "info")
        return redirect(url_for("cart"))

    order = sync_order_with_cart(current_user, cart)
    db.session.commit()
    summary = build_order_summary(order)
    return render_template(
        "checkout.html",
        cart=cart,
        order=order,
        checkout_items=summary["items"],
        checkout_subtotal=summary["subtotal"],
        checkout_total=summary["total"],
        checkout_item_count=summary["item_count"],
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


@app.route("/plants/new", methods=['GET', 'POST'])
def create_plant():
    if request.method == 'POST':
        plant = Plant(
            common_name=request.form['common_name'],
            scientific_name=request.form.get('scientific_name'),
            category_id=request.form.get('category_id'),
            species_id=request.form.get('species_id'),
            variety_id=request.form.get('variety_id'),
            description=request.form.get('description'),
            colour=request.form.get('colour'),
            growth_width=request.form.get('growth_width'),
            growth_height=request.form.get('growth_height'),
            fragrant=request.form.get('fragrant') == 'true',
            frost_sensitive=request.form.get('frost_sensitive') == 'true',
            flowering_period=request.form.get('flowering_period'),
            light_requirements=request.form.get('light_requirements'),
            soil_requirements=request.form.get('soil_requirements'),
            planting_advice=request.form.get('planting_advice'),
            watering_needs=request.form.get('watering_needs'),
            pruning_needs=request.form.get('pruning_needs'),
        )
        db.session.add(plant)
        db.session.commit()

        return redirect(url_for('plant_detail', id=plant.id))
    return render_template('create_plant.html')

@app.route("/plants/<int:id>")
def plant_detail(id):
    plant = Plant.query.get_or_404(id)
    category = Category.query.get(plant.category_id) if plant.category_id else None
    species = Species.query.get(plant.species_id) if plant.species_id else None
    variety = Variety.query.get(plant.variety_id) if plant.variety_id else None
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

@app.route("/delete/<int:id>", methods=['POST'])
def delete_plant(id):
    plant = Plant.query.get_or_404(id)
    db.session.delete(plant)
    db.session.commit()
    return redirect(url_for('home'))

@app.route("/edit/<int:id>", methods=['GET', 'POST'])
def edit_plant(id):
    plant = Plant.query.get_or_404(id)
    if request.method == 'POST':
        for field, value in request.form.items():
            setattr(plant, field, value)
        db.session.commit()
        return redirect(url_for('plant_detail', id=plant.id))
    return render_template('edit_plant.html', plant=plant)

#add category
@app.route("/categories/new", methods=['GET', 'POST'])
def create_category():
    if request.method == 'POST':
        
        image_filename = save_image(request.files['image'])
        
        category = Category(
            name=request.form['name'],
            image_filename=image_filename,
            description=request.form.get('description')
        )
        db.session.add(category)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('create_category.html')

#add species
@app.route("/species/new", methods=['GET', 'POST'])
def create_species():
    if request.method == 'POST':
        species = Species(
            name=request.form['name'],
            description=request.form.get('description')
        )
        db.session.add(species)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('create_species.html')

#add variety
@app.route("/varieties/new", methods=['GET', 'POST'])
def create_variety():
    if request.method == 'POST':
        variety = Variety(
            name=request.form['name'],
            description=request.form.get('description')
        )
        db.session.add(variety)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('create_variety.html')


@app.route("/categories/<int:id>")
def category_detail(id):
    category = Category.query.get_or_404(id)
    plants = Plant.query.filter_by(category_id=id).order_by(Plant.common_name).all()
    return render_template(
        "catalog_detail.html",
        title="Category",
        item=category,
        plants=plants,
        item_count=len(plants),
        back_url=url_for("categories_index"),
    )


@app.route("/species/<int:id>")
def species_detail(id):
    item = Species.query.get_or_404(id)
    plants = Plant.query.filter_by(species_id=id).order_by(Plant.common_name).all()
    return render_template(
        "catalog_detail.html",
        title="Species",
        item=item,
        plants=plants,
        item_count=len(plants),
        back_url=url_for("species_index"),
    )


@app.route("/varieties/<int:id>")
def variety_detail(id):
    item = Variety.query.get_or_404(id)
    plants = Plant.query.filter_by(variety_id=id).order_by(Plant.common_name).all()
    return render_template(
        "catalog_detail.html",
        title="Variety",
        item=item,
        plants=plants,
        item_count=len(plants),
        back_url=url_for("varieties_index"),
    )
