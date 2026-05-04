import os
import uuid
from functools import wraps
from flask import Blueprint, abort, flash, render_template, request, redirect, url_for
from flask_login import current_user, login_required

PLANT_IMAGE_DIR = os.path.join("static", "images", "plants")
_ALLOWED_EXTS = {"png", "jpg", "jpeg", "webp"}


def _save_plant_image(file):
    ext = file.filename.rsplit(".", 1)[-1].lower()
    filename = f"plants/{uuid.uuid4().hex}.{ext}"
    os.makedirs(PLANT_IMAGE_DIR, exist_ok=True)
    file.save(os.path.join("static", "images", filename))
    return filename

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def staff_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not current_user.is_staff:
            abort(403)
        return f(*args, **kwargs)
    return decorated

@admin_bp.route("/home")
@staff_required
def home():
    from models import Order, Plant
    total_orders = Order.query.count()
    pending_orders = Order.query.filter_by(status="pending").count()
    total_plants = Plant.query.count()
    return render_template(
        "admin/home.html",
        total_orders=total_orders,
        pending_orders=pending_orders,
        total_plants=total_plants,
    )


@admin_bp.route("/plants")
@staff_required
def plants():
    from models import Plant
    plants = Plant.query.order_by(Plant.common_name).all()
    return render_template("admin/plants.html", plants=plants)


@admin_bp.route("/plants/new", methods=["GET", "POST"])
@staff_required
def create_plant():
    from app import db
    from models import Plant, Category, Species, Variety

    if request.method == "POST":
        plant = Plant(
            common_name=request.form["common_name"],
            scientific_name=request.form.get("scientific_name"),
            category_id=request.form.get("category_id") or None,
            species_id=request.form.get("species_id") or None,
            variety_id=request.form.get("variety_id") or None,
            description=request.form.get("description"),
            colour=request.form.get("colour"),
            growth_width=request.form.get("growth_width") or None,
            growth_height=request.form.get("growth_height") or None,
            fragrant=request.form.get("fragrant") == "true",
            frost_sensitive=request.form.get("frost_sensitive") == "true",
            flowering_period=request.form.get("flowering_period"),
            light_requirements=request.form.get("light_requirements"),
            soil_requirements=request.form.get("soil_requirements"),
            planting_advice=request.form.get("planting_advice"),
            watering_needs=request.form.get("watering_needs"),
            pruning_needs=request.form.get("pruning_needs"),
        )
        db.session.add(plant)
        db.session.commit()
        return redirect(url_for("admin.plant_detail", id=plant.id))

    categories = Category.query.order_by(Category.name).all()
    species = Species.query.order_by(Species.name).all()
    varieties = Variety.query.order_by(Variety.name).all()
    return render_template(
        "admin/plant_form.html",
        plant=None,
        categories=categories,
        species=species,
        varieties=varieties,
    )


PLANT_FIELDS = [
    "common_name", "scientific_name", "description", "colour",
    "flowering_period", "light_requirements", "soil_requirements",
    "planting_advice", "watering_needs", "pruning_needs",
]


@admin_bp.route("/plants/<int:id>", methods=["GET", "POST"])
@staff_required
def plant_detail(id):
    from app import db
    from models import Plant, Category, Species, Variety, Pot

    plant = Plant.query.get_or_404(id)

    if request.method == "POST":
        for field in PLANT_FIELDS:
            setattr(plant, field, request.form.get(field))

        plant.category_id = request.form.get("category_id") or None
        plant.species_id = request.form.get("species_id") or None
        plant.variety_id = request.form.get("variety_id") or None
        plant.growth_width = request.form.get("growth_width") or None
        plant.growth_height = request.form.get("growth_height") or None
        plant.fragrant = request.form.get("fragrant") == "true"
        plant.frost_sensitive = request.form.get("frost_sensitive") == "true"

        db.session.commit()
        return redirect(url_for("admin.plant_detail", id=plant.id))

    categories = Category.query.order_by(Category.name).all()
    species = Species.query.order_by(Species.name).all()
    varieties = Variety.query.order_by(Variety.name).all()
    assigned_pot_ids = {pp.pot_id for pp in plant.plant_pots}
    available_pots = [p for p in Pot.query.order_by(Pot.size).all() if p.id not in assigned_pot_ids]
    return render_template(
        "admin/plant_detail.html",
        plant=plant,
        categories=categories,
        species=species,
        varieties=varieties,
        available_pots=available_pots,
    )


@admin_bp.route("/plants/<int:id>/delete", methods=["POST"])
@staff_required
def delete_plant(id):
    from app import db
    from models import Plant

    plant = Plant.query.get_or_404(id)
    db.session.delete(plant)
    db.session.commit()
    return redirect(url_for("admin.plants"))

@admin_bp.route("/plants/<int:id>/assign-pot", methods=["POST"])
@staff_required
def assign_pot(id):
    from app import db
    from models import Plant, PlantPot

    Plant.query.get_or_404(id)
    pot_id = request.form.get("pot_id", type=int)
    price = request.form.get("price") or None
    stock_qty = request.form.get("stock_qty", type=int) or 0

    plant_pot = PlantPot(plant_id=id, pot_id=pot_id, price=price, stock_qty=stock_qty)
    db.session.add(plant_pot)
    db.session.commit()
    return redirect(url_for("admin.plant_detail", id=id))


@admin_bp.route("/plants/<int:id>/unassign-pot/<int:pot_id>", methods=["POST"])
@staff_required
def unassign_pot(id, pot_id):
    from app import db
    from models import PlantPot

    plant_pot = PlantPot.query.get_or_404((id, pot_id))
    db.session.delete(plant_pot)
    db.session.commit()
    return redirect(url_for("admin.plant_detail", id=id))


@admin_bp.route("/pots")
@staff_required
def pots():
    from models import Pot
    pots = Pot.query.order_by(Pot.size).all()
    return render_template("admin/pots.html", pots=pots)


@admin_bp.route("/pots/new", methods=["GET", "POST"])
@staff_required
def create_pot():
    from app import db
    from models import Pot
    if request.method == "POST":
        pot = Pot(
            size=request.form.get("size"),
        )
        db.session.add(pot)
        db.session.commit()
        return redirect(url_for("admin.pots"))

    return render_template("admin/pot_form.html", pot=None)


@admin_bp.route("/pots/<int:id>/edit", methods=["GET", "POST"])
@staff_required
def edit_pot(id):
    from app import db
    from models import Pot

    pot = Pot.query.get_or_404(id)
    if request.method == "POST":
        pot.size = request.form.get("size")
        db.session.commit()
        return redirect(url_for("admin.pots"))

    return render_template("admin/pot_form.html", pot=pot)


@admin_bp.route("/pots/<int:id>/delete", methods=["POST"])
@staff_required
def delete_pot(id):
    from app import db
    from models import Pot

    pot = Pot.query.get_or_404(id)
    db.session.delete(pot)
    db.session.commit()
    return redirect(url_for("admin.pots"))


@admin_bp.route("/orders")
@staff_required
def orders():
    from models import Order
    orders = Order.query.order_by(Order.id).all()
    return render_template("admin/orders.html", orders=orders)


@admin_bp.route("/categories")
@staff_required
def categories():
    from models import Category, Species, Variety
    categories = Category.query.order_by(Category.name).all()
    species = Species.query.order_by(Species.name).all()
    varieties = Variety.query.order_by(Variety.name).all()
    return render_template("admin/categories.html", categories=categories, species=species, varieties=varieties)


@admin_bp.route("/categories/new", methods=["GET", "POST"])
@staff_required
def create_category():
    from app import db
    from models import Category
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Category name is required.", "error")
            return redirect(url_for("admin.categories"))

        category = Category(
            name=name,
            description=request.form.get("description"),
        )
        db.session.add(category)
        db.session.commit()
        flash("Category added.", "success")
    return redirect(url_for("admin.categories"))


@admin_bp.route("/categories/<int:id>/update", methods=["POST"])
@staff_required
def update_category(id):
    from app import db
    from models import Category

    category = Category.query.get_or_404(id)
    name = request.form.get("name", "").strip()
    if not name:
        flash("Category name is required.", "error")
        return redirect(url_for("admin.categories"))

    category.name = name
    category.description = request.form.get("description", "").strip() or None
    db.session.commit()
    flash("Category updated.", "success")
    return redirect(url_for("admin.categories"))


@admin_bp.route("/categories/<int:id>/delete", methods=["POST"])
@staff_required
def delete_category(id):
    from app import db
    from models import Category, Plant

    category = Category.query.get_or_404(id)
    if Plant.query.filter_by(category_id=id).first():
        flash("Category cannot be deleted while plants are using it.", "error")
        return redirect(url_for("admin.categories"))

    db.session.delete(category)
    db.session.commit()
    flash("Category deleted.", "success")
    return redirect(url_for("admin.categories"))


@admin_bp.route("/species/new", methods=["GET", "POST"])
@staff_required
def create_species():
    from app import db
    from models import Species
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Species name is required.", "error")
            return redirect(url_for("admin.categories"))

        species = Species(
            name=name,
            description=request.form.get("description"),
        )
        db.session.add(species)
        db.session.commit()
        flash("Species added.", "success")
    return redirect(url_for("admin.categories"))


@admin_bp.route("/species/<int:id>/update", methods=["POST"])
@staff_required
def update_species(id):
    from app import db
    from models import Species

    species = Species.query.get_or_404(id)
    name = request.form.get("name", "").strip()
    if not name:
        flash("Species name is required.", "error")
        return redirect(url_for("admin.categories"))

    species.name = name
    species.description = request.form.get("description", "").strip() or None
    db.session.commit()
    flash("Species updated.", "success")
    return redirect(url_for("admin.categories"))


@admin_bp.route("/species/<int:id>/delete", methods=["POST"])
@staff_required
def delete_species(id):
    from app import db
    from models import Plant, Species

    species = Species.query.get_or_404(id)
    if Plant.query.filter_by(species_id=id).first():
        flash("Species cannot be deleted while plants are using it.", "error")
        return redirect(url_for("admin.categories"))

    db.session.delete(species)
    db.session.commit()
    flash("Species deleted.", "success")
    return redirect(url_for("admin.categories"))


@admin_bp.route("/varieties/new", methods=["GET", "POST"])
@staff_required
def create_variety():
    from app import db
    from models import Variety
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Variety name is required.", "error")
            return redirect(url_for("admin.categories"))

        variety = Variety(
            name=name,
            description=request.form.get("description"),
        )
        db.session.add(variety)
        db.session.commit()
        flash("Variety added.", "success")
    return redirect(url_for("admin.categories"))


@admin_bp.route("/varieties/<int:id>/update", methods=["POST"])
@staff_required
def update_variety(id):
    from app import db
    from models import Variety

    variety = Variety.query.get_or_404(id)
    name = request.form.get("name", "").strip()
    if not name:
        flash("Variety name is required.", "error")
        return redirect(url_for("admin.categories"))

    variety.name = name
    variety.description = request.form.get("description", "").strip() or None
    db.session.commit()
    flash("Variety updated.", "success")
    return redirect(url_for("admin.categories"))


@admin_bp.route("/varieties/<int:id>/delete", methods=["POST"])
@staff_required
def delete_variety(id):
    from app import db
    from models import Plant, Variety

    variety = Variety.query.get_or_404(id)
    if Plant.query.filter_by(variety_id=id).first():
        flash("Variety cannot be deleted while plants are using it.", "error")
        return redirect(url_for("admin.categories"))

    db.session.delete(variety)
    db.session.commit()
    flash("Variety deleted.", "success")
    return redirect(url_for("admin.categories"))


@admin_bp.route("/plants/<int:id>/images/upload", methods=["POST"])
@staff_required
def upload_plant_images(id):
    from app import db
    from models import Plant

    plant = Plant.query.get_or_404(id)
    files = request.files.getlist("images")
    new_images = []
    for file in files:
        if file and file.filename and file.filename.rsplit(".", 1)[-1].lower() in _ALLOWED_EXTS:
            new_images.append(_save_plant_image(file))

    plant.images = (plant.images or []) + new_images
    db.session.commit()
    return redirect(url_for("admin.plant_detail", id=id))


@admin_bp.route("/plants/<int:id>/images/delete", methods=["POST"])
@staff_required
def delete_plant_image(id):
    from app import db
    from models import Plant

    plant = Plant.query.get_or_404(id)
    filename = request.form.get("filename")
    file_path = os.path.join("static", "images", filename) if filename else None

    plant.images = [f for f in (plant.images or []) if f != filename]
    db.session.commit()

    if file_path and os.path.exists(file_path):
        os.remove(file_path)

    return redirect(url_for("admin.plant_detail", id=id))


@admin_bp.route("/plants/<int:id>/pots/<int:pot_id>/update", methods=["POST"])
@staff_required
def update_pot(id, pot_id):
    from app import db
    from models import PlantPot

    plant_pot = PlantPot.query.get_or_404((id, pot_id))
    stock_qty = request.form.get("stock_qty", type=int)
    price = request.form.get("price")

    if stock_qty is None or stock_qty < 0:
        flash("Invalid stock quantity.", "error")
        return redirect(url_for("admin.plant_detail", id=id) + "#pot-sizes")

    plant_pot.stock_qty = stock_qty
    if price:
        plant_pot.price = price
    db.session.commit()
    flash("Pot updated.", "success")
    return redirect(url_for("admin.plant_detail", id=id) + "#pot-sizes")


@admin_bp.route("/plants/<int:id>/images/reorder", methods=["POST"])
@staff_required
def reorder_plant_images(id):
    from app import db
    from models import Plant

    plant = Plant.query.get_or_404(id)
    ordered = request.form.getlist("images[]")
    existing = set(plant.images or [])
    plant.images = [f for f in ordered if f in existing]
    db.session.commit()
    return redirect(url_for("admin.plant_detail", id=id))

