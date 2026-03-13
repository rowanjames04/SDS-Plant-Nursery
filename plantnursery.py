import os
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DB_URI')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

db = SQLAlchemy(app)
migrate = Migrate(app, db)

class Plant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    common_name = db.Column(db.String(100), nullable=False)
    scientific_name = db.Column(db.String(100))
    size = db.Column(db.Integer)
    category = db.Column(db.String(100))
    species = db.Column(db.String(100))
    variety = db.Column(db.String(100))
    pot_container = db.Column(db.String(100))
    price = db.Column(db.Float, default=0.00)
    description = db.Column(db.String(200))
    #key info
    colour = db.Column(db.String(50))
    growth_width = db.Column(db.Float)
    growth_height = db.Column(db.Float)
    fragrant = db.Column(db.Boolean, default=False)
    frost_sensitive = db.Column(db.Boolean, default=False)
    flowering_period = db.Column(db.String(200))
    light_requirements = db.Column(db.String(200))
    soil_requirements = db.Column(db.String(200))
    #care advice
    planting_advice = db.Column(db.String(200))
    watering_needs = db.Column(db.String(200))
    pruning_needs = db.Column(db.String(200))
    
    
@app.route("/")
def home():
    return render_template('Home.html')

@app.route("/login")
def login():
    return render_template('Login.html')

@app.route("/register")
def register():
    return render_template('Register.html')