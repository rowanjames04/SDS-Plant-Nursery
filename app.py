import os
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv


load_dotenv()

app = Flask(__name__, instance_relative_config=True)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DB_URI', 'sqlite:///plants.db')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

db = SQLAlchemy(app)
migrate = Migrate(app, db)

from models import Plant, User
    
@app.route("/")
def home():
    return render_template('Home.html', plants=plants)

@app.route("/login")
def login():
    return render_template('Login.html')

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
            category=request.form.get('category'),
            species=request.form.get('species'),
            variety=request.form.get('variety'),
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

