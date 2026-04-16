from functools import wraps
from flask import Blueprint, abort, render_template, request, redirect, url_for
from flask_login import current_user, login_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def staff_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not current_user.is_staff:
            abort(403)
        return f(*args, **kwargs)
    return decorated


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
        return redirect(url_for("admin.plants"))

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


@admin_bp.route("/plants/<int:id>/edit", methods=["GET", "POST"])
@staff_required
def edit_plant(id):
    from app import db
    from models import Plant, Category, Species, Variety

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
        return redirect(url_for("admin.plants"))

    categories = Category.query.order_by(Category.name).all()
    species = Species.query.order_by(Species.name).all()
    varieties = Variety.query.order_by(Variety.name).all()
    return render_template(
        "admin/plant_form.html",
        plant=plant,
        categories=categories,
        species=species,
        varieties=varieties,
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
