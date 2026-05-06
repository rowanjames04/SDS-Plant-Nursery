import os
import uuid
from functools import wraps
from flask import Blueprint, abort, flash, render_template, request, redirect, url_for
from flask_login import current_user, login_required

from app import db
from models import Category, Order, Plant, PlantPot, Pot, Species, Variety

PLANT_IMAGE_DIR = os.path.join("static", "images", "plants")
_ALLOWED_EXTS = {"png", "jpg", "jpeg", "webp"}


def _save_plant_image(file):
    ext = file.filename.rsplit(".", 1)[-1].lower()
    filename = f"plants/{uuid.uuid4().hex}.{ext}"
    os.makedirs(PLANT_IMAGE_DIR, exist_ok=True)
    file.save(os.path.join("static", "images", filename))
    return filename

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def _taxonomy_form_data(label):
    name = request.form.get("name", "").strip()
    if not name:
        flash(f"{label} name is required.", "error")
        return None
    return {
        "name": name,
        "description": request.form.get("description", "").strip() or None,
    }


def _plant_counts_for(column):
    return dict(
        db.session.query(column, db.func.count(Plant.id))
        .filter(column.isnot(None))
        .group_by(column)
        .all()
    )


def _filter_taxonomy_records(records, query):
    if not query:
        return records

    query = query.lower()
    return [
        record for record in records
        if query in " ".join([record.name or "", record.description or ""]).lower()
    ]


def _create_taxonomy_record(model, label):
    data = _taxonomy_form_data(label)
    if data:
        db.session.add(model(**data))
        db.session.commit()
        flash(f"{label} added.", "success")
    return redirect(url_for("admin.categories"))


def _update_taxonomy_record(model, record_id, label):
    record = model.query.get_or_404(record_id)
    data = _taxonomy_form_data(label)
    if not data:
        return redirect(url_for("admin.categories"))

    record.name = data["name"]
    record.description = data["description"]
    db.session.commit()
    flash(f"{label} updated.", "success")
    return redirect(url_for("admin.categories"))


def _delete_taxonomy_record(model, record_id, plant_column, label):
    record = model.query.get_or_404(record_id)
    if Plant.query.filter(plant_column == record_id).first():
        flash(f"{label} cannot be deleted while plants are using it.", "error")
        return redirect(url_for("admin.categories"))

    db.session.delete(record)
    db.session.commit()
    flash(f"{label} deleted.", "success")
    return redirect(url_for("admin.categories"))


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
    categories = Category.query.all()
    category_map = {category.id: category.name for category in categories}
    search_query = request.args.get("q", "").strip()
    plants = Plant.query.order_by(Plant.common_name).all()
    plant_rows = []
    for plant in plants:
        category_name = category_map.get(plant.category_id)
        if search_query:
            searchable_text = " ".join(
                [
                    plant.common_name or "",
                    category_name or "",
                ]
            ).lower()
            if search_query.lower() not in searchable_text:
                continue

        plant_rows.append(
            {
                "id": plant.id,
                "common_name": plant.common_name,
                "category_name": category_name,
                "assigned_pot_count": len(plant.plant_pots),
                "total_stock": sum(plant_pot.stock_qty for plant_pot in plant.plant_pots),
            }
        )
    return render_template(
        "admin/plants.html",
        plants=plant_rows,
        total_plants=len(plants),
        search_query=search_query,
    )


@admin_bp.route("/plants/new", methods=["GET", "POST"])
@staff_required
def create_plant():
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
    plant = Plant.query.get_or_404(id)
    db.session.delete(plant)
    db.session.commit()
    return redirect(url_for("admin.plants"))

@admin_bp.route("/plants/<int:id>/assign-pot", methods=["POST"])
@staff_required
def assign_pot(id):
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
    plant_pot = PlantPot.query.get_or_404((id, pot_id))
    db.session.delete(plant_pot)
    db.session.commit()
    return redirect(url_for("admin.plant_detail", id=id))


@admin_bp.route("/pots")
@staff_required
def pots():
    search_query = request.args.get("q", "").strip()
    pots = Pot.query.order_by(Pot.size).all()
    if search_query:
        pots = [
            pot for pot in pots
            if search_query.lower() in f"{pot.size}mm".lower()
        ]
    return render_template("admin/pots.html", pots=pots, search_query=search_query)


@admin_bp.route("/pots/new", methods=["GET", "POST"])
@staff_required
def create_pot():
    if request.method != "POST":
        return redirect(url_for("admin.pots"))

    size = request.form.get("size", type=int)
    if size is None or size <= 0:
        flash("Pot size must be a positive number.", "error")
        return redirect(url_for("admin.pots"))

    if Pot.query.filter_by(size=size).first():
        flash("That pot size already exists.", "error")
        return redirect(url_for("admin.pots"))

    db.session.add(Pot(size=size))
    db.session.commit()
    flash("Pot size added.", "success")
    return redirect(url_for("admin.pots"))


@admin_bp.route("/pots/<int:id>/edit", methods=["GET", "POST"])
@staff_required
def edit_pot(id):
    pot = Pot.query.get_or_404(id)
    if request.method != "POST":
        return redirect(url_for("admin.pots"))

    size = request.form.get("size", type=int)
    if size is None or size <= 0:
        flash("Pot size must be a positive number.", "error")
        return redirect(url_for("admin.pots"))

    existing = Pot.query.filter_by(size=size).first()
    if existing and existing.id != pot.id:
        flash("That pot size already exists.", "error")
        return redirect(url_for("admin.pots"))

    pot.size = size
    db.session.commit()
    flash("Pot size updated.", "success")
    return redirect(url_for("admin.pots"))


@admin_bp.route("/pots/<int:id>/delete", methods=["POST"])
@staff_required
def delete_pot(id):
    pot = Pot.query.get_or_404(id)
    if pot.plant_pots:
        flash("Pot size cannot be deleted while plants are using it.", "error")
        return redirect(url_for("admin.pots"))

    db.session.delete(pot)
    db.session.commit()
    flash("Pot size deleted.", "success")
    return redirect(url_for("admin.pots"))


@admin_bp.route("/orders")
@staff_required
def orders():
    orders = Order.query.order_by(Order.id).all()
    return render_template("admin/orders.html", orders=orders)


@admin_bp.route("/categories")
@staff_required
def categories():
    search_query = request.args.get("q", "").strip()
    categories = Category.query.order_by(Category.name).all()
    species = Species.query.order_by(Species.name).all()
    varieties = Variety.query.order_by(Variety.name).all()
    return render_template(
        "admin/categories.html",
        categories=_filter_taxonomy_records(categories, search_query),
        species=_filter_taxonomy_records(species, search_query),
        varieties=_filter_taxonomy_records(varieties, search_query),
        search_query=search_query,
        category_counts=_plant_counts_for(Plant.category_id),
        species_counts=_plant_counts_for(Plant.species_id),
        variety_counts=_plant_counts_for(Plant.variety_id),
    )


@admin_bp.route("/categories/new", methods=["GET", "POST"])
@staff_required
def create_category():
    if request.method != "POST":
        return redirect(url_for("admin.categories"))
    return _create_taxonomy_record(Category, "Category")


@admin_bp.route("/categories/<int:id>/update", methods=["POST"])
@staff_required
def update_category(id):
    return _update_taxonomy_record(Category, id, "Category")


@admin_bp.route("/categories/<int:id>/delete", methods=["POST"])
@staff_required
def delete_category(id):
    return _delete_taxonomy_record(Category, id, Plant.category_id, "Category")


@admin_bp.route("/species/new", methods=["GET", "POST"])
@staff_required
def create_species():
    if request.method != "POST":
        return redirect(url_for("admin.categories"))
    return _create_taxonomy_record(Species, "Species")


@admin_bp.route("/species/<int:id>/update", methods=["POST"])
@staff_required
def update_species(id):
    return _update_taxonomy_record(Species, id, "Species")


@admin_bp.route("/species/<int:id>/delete", methods=["POST"])
@staff_required
def delete_species(id):
    return _delete_taxonomy_record(Species, id, Plant.species_id, "Species")


@admin_bp.route("/varieties/new", methods=["GET", "POST"])
@staff_required
def create_variety():
    if request.method != "POST":
        return redirect(url_for("admin.categories"))
    return _create_taxonomy_record(Variety, "Variety")


@admin_bp.route("/varieties/<int:id>/update", methods=["POST"])
@staff_required
def update_variety(id):
    return _update_taxonomy_record(Variety, id, "Variety")


@admin_bp.route("/varieties/<int:id>/delete", methods=["POST"])
@staff_required
def delete_variety(id):
    return _delete_taxonomy_record(Variety, id, Plant.variety_id, "Variety")


@admin_bp.route("/plants/<int:id>/images/upload", methods=["POST"])
@staff_required
def upload_plant_images(id):
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
    plant = Plant.query.get_or_404(id)
    ordered = request.form.getlist("images[]")
    existing = set(plant.images or [])
    plant.images = [f for f in ordered if f in existing]
    db.session.commit()
    return redirect(url_for("admin.plant_detail", id=id))

