import os
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from flask_migrate import Migrate
from dotenv import load_dotenv


load_dotenv()

app = Flask(__name__, instance_relative_config=True)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DB_URI', 'sqlite:///nursery.db')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

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

with app.app_context():
    # Create any missing tables for a fresh local SQLite database.
    db.create_all()
    
@app.route("/")
def home():
    categories = Category.query.all()
    return render_template('Home.html', categories=categories)

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
        plant = Plant(
            common_name=request.form['common_name'],
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
    return render_template('plant_detail.html', plant=plant)

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
        category = Category(
            name=request.form['name'],
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
