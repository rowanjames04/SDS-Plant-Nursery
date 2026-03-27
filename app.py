import os
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from flask_migrate import Migrate
from dotenv import load_dotenv
from werkzeug.utils import secure_filename


load_dotenv()
UPLOAD_FOLDER = 'static/images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
MAX_CONTENT_LENGTH = 16 * 1000 * 1000  # 16 MB lmit for uploaded images

app = Flask(__name__, instance_relative_config=True)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DB_URI', 'sqlite:///nursery.db')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
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

from models import Category, Plant, Species, User, Variety
    
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
            "size": plant.size,
            "category_name": category_map.get(plant.category_id),
            "species_name": species_map.get(plant.species_id),
            "variety_name": variety_map.get(plant.variety_id),
            "pot_container": plant.pot_container,
            "price": plant.price,
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
            "image_filename": plant.image_filename,
        })

    return {
        "categories": categories,
        "species": species,
        "varieties": varieties,
        "plants": plant_rows,
    }


with app.app_context():
    # Create any missing tables for a fresh local SQLite database.
    db.create_all()
    
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


@app.route("/categories")
def categories_index():
    categories = Category.query.order_by(Category.name).all()
    counts = {item.id: Plant.query.filter_by(category_id=item.id).count() for item in categories}
    return render_template(
        "catalog_index.html",
        title="Categories",
        subtitle="Browse the nursery by plant group.",
        items=categories,
        detail_label="category_detail",
        counts=counts,
    )


@app.route("/species")
def species_index():
    species = Species.query.order_by(Species.name).all()
    counts = {item.id: Plant.query.filter_by(species_id=item.id).count() for item in species}
    return render_template(
        "catalog_index.html",
        title="Species",
        subtitle="Browse by botanical species.",
        items=species,
        detail_label="species_detail",
        counts=counts,
    )


@app.route("/varieties")
def varieties_index():
    varieties = Variety.query.order_by(Variety.name).all()
    counts = {item.id: Plant.query.filter_by(variety_id=item.id).count() for item in varieties}
    return render_template(
        "catalog_index.html",
        title="Varieties",
        subtitle="Browse the named plant varieties we have on hand.",
        items=varieties,
        detail_label="variety_detail",
        counts=counts,
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
def profile():
    return render_template('profile.html')

@app.route("/login")
def login():
    return render_template('Login.html')

@app.route("/wishlist")
def wishlist():
    return render_template(
        "wishlist.html",
        wishlist_items=[],
    )

@app.route("/cart")
def cart():
    return render_template(
        "cart.html",
        cart_items=[],
    )

@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user = User(
            email=request.form['email'],
            full_name=request.form['full_name'],
            password=request.form['password']
        )
    return render_template('Register.html')


@app.route("/plants/new", methods=['GET', 'POST'])
def create_plant():
    if request.method == 'POST':
        image_filename = save_image(request.files['image'])
        
        plant = Plant(
            common_name=request.form['common_name'],
            image_filename=image_filename,
            scientific_name=request.form.get('scientific_name'),
            size=request.form.get('size'),
            category_id=request.form.get('category_id'),
            species_id=request.form.get('species_id'),
            variety_id=request.form.get('variety_id'),
            pot_container=request.form.get('pot_container'),
            price=request.form.get('price'),
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
    return render_template(
        'plant_detail.html',
        plant=plant,
        category=category,
        species=species,
        variety=variety,
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
